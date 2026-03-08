import httpx
from httpx import URL, Headers

from src.domain.models.mail import Mail
from src.logger import get_logger
from src.settings import settings

logger = get_logger(__name__)

NOTION_PAGES_URL = URL("https://api.notion.com/v1/pages")
NOTION_VERSION = "2025-09-03"
NOTION_RICH_TEXT_LIMIT = 2000

HEADERS = Headers(
    {
        "Authorization": f"Bearer {settings.notion_api_key}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,
    }
)


class NotionClient:
    def post_mail(self, mail: Mail) -> None:
        if self._title_exists(mail.subject):
            logger.info("Skipping: page with title '%s' already exists in Notion DB", mail.subject)
            return
        notion_data = {
            "parent": {"type": "data_source_id", "data_source_id": settings.notion_data_source_id},
            "properties": {
                "Name": {"title": [{"text": {"content": mail.subject}}]},
            },
            "children": self._split_into_paragraph_blocks(mail.body),
        }
        with httpx.Client(headers=HEADERS, timeout=20.0) as client:
            res = client.post(NOTION_PAGES_URL, json=notion_data)
        if res.is_success:
            return
        logger.error("Notion API error: %s\nResponse body: %s", res.status_code, res.text)
        res.raise_for_status()

    def _title_exists(self, title: str) -> bool:
        query_url = URL(f"https://api.notion.com/v1/data_sources/{settings.notion_data_source_id}/query")
        query_data = {
            "filter": {
                "property": "Name",
                "title": {"equals": title},
            }
        }
        with httpx.Client(headers=HEADERS, timeout=20.0) as client:
            res = client.post(query_url, json=query_data)
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
            for i in range(0, max(len(text), 1), NOTION_RICH_TEXT_LIMIT)
        ]
