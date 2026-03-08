import httpx
from httpx import URL, Headers

from domain.models.mail import Mail
from settings import settings

NOTION_URL = URL("https://api.notion.com/v1/pages")
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
        notion_data = {
            "parent": {"type": "data_source_id", "data_source_id": settings.notion_data_source_id},
            "properties": {
                "Name": {"title": [{"text": {"content": mail.subject}}]},
            },
            "children": self._split_into_paragraph_blocks(mail.body),
        }
        with httpx.Client(headers=HEADERS) as client:
            res = client.post(NOTION_URL, json=notion_data)
        if res.is_success:
            return
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
