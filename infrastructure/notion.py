import httpx

from domain.mail import Mail
from settings import settings

NOTION_URL = httpx.URL("https://api.notion.com/v1/pages")
NOTION_VERSION = "2025-09-03"
NOTION_RICH_TEXT_LIMIT = 2000

HEADERS = httpx.Headers(
    {
        "Authorization": f"Bearer {settings.notion_api_key}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,
    }
)


class NotionClient:
    def post_mail(self, mail: Mail) -> None:
        notion_data = {
            "parent": {"type": "data_source_id", "data_source_id": settings.notion_data_source_id},
            "properties": {
                "Name": {"title": [{"text": {"content": mail.subject}}]},
            },
            "children": self._split_into_paragraph_blocks(mail.body),
        }
        res = httpx.post(NOTION_URL, headers=HEADERS, json=notion_data, timeout=20.0)
        if not res.is_success:
            print(f"Notion API error: {res.status_code}")
            print(f"Response body: {res.text}")
        res.raise_for_status()

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
