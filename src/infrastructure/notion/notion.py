import httpx
from httpx import URL, Headers

from src.domain.models.mail import Mail
from src.logger import get_logger

logger = get_logger(__name__)

NOTION_PAGES_URL = URL("https://api.notion.com/v1/pages")
NOTION_VERSION = "2025-09-03"
NOTION_RICH_TEXT_LIMIT = 2000

TITLE_PROPERTY_NAME = "Name"


class NotionClient:
    def __init__(self, api_key: str, data_source_id: str) -> None:
        self.data_source_id = data_source_id
        self.headers = Headers(
            {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Notion-Version": NOTION_VERSION,
            }
        )

    def export(self, mail: Mail) -> None:
        if self._title_exists(mail.subject):
            logger.info("Skipping: page with title '%s' already exists in Notion DB", mail.subject)
            return
        notion_data = {
            "parent": {"type": "data_source_id", "data_source_id": self.data_source_id},
            "properties": {
                TITLE_PROPERTY_NAME: {"title": [{"text": {"content": mail.subject}}]},
            },
            "children": self._split_into_paragraph_blocks(mail.body),
        }
        with httpx.Client(headers=self.headers, timeout=20.0) as client:
            res = client.post(NOTION_PAGES_URL, json=notion_data, timeout=20.0)
        if res.is_success:
            return
        logger.error("Notion API error: %s\nResponse body: %s", res.status_code, res.text)
        res.raise_for_status()

    def _title_exists(self, title: str) -> bool:
        url = URL(f"https://api.notion.com/v1/data_sources/{self.data_source_id}/query")
        data = {
            "filter": {
                "property": TITLE_PROPERTY_NAME,
                "title": {"equals": title},
            }
        }
        with httpx.Client(headers=self.headers, timeout=20.0) as client:
            res = client.post(url, json=data, timeout=20.0)
        if not res.is_success:
            logger.error("Notion query error: %s\nResponse body: %s", res.status_code, res.text)
            res.raise_for_status()
        return len(res.json().get("results", [])) > 0

    def _split_into_paragraph_blocks(self, text: str) -> list[dict]:
        if not text:
            return []
        return [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": text[i : i + NOTION_RICH_TEXT_LIMIT]}}]},
            }
            for i in range(0, len(text), NOTION_RICH_TEXT_LIMIT)
        ]
