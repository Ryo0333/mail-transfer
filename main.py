import email
import imaplib
import os

import httpx
from dotenv import load_dotenv

load_dotenv()

IMAP_SERVER = "imap.gmail.com"
GMAIL_USERNAME = os.getenv("GMAIL_USERNAME")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
NOTION_URL = httpx.URL("https://api.notion.com/v1/pages")

FROM_EMAIL = os.getenv("FROM_EMAIL")

HEADERS = httpx.Headers(
    {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }
)


def mail_transfer() -> None:
    gmail = imaplib.IMAP4_SSL(IMAP_SERVER)
    if GMAIL_USERNAME is None:
        raise ValueError("GMAIL_USERNAME is not set")
    if GMAIL_APP_PASSWORD is None:
        raise ValueError("GMAIL_APP_PASSWORD is not set")
    gmail.login(GMAIL_USERNAME, GMAIL_APP_PASSWORD)
    gmail.select("inbox")

    if FROM_EMAIL is None:
        raise ValueError("FROM_EMAIL is not set")

    _, data = gmail.search(None, f"FROM {FROM_EMAIL}")

    for num in data[0].split():
        print(f"Processing mail: {num}")
        h, d = gmail.fetch(num, "(RFC822)")
        raw_email = d[0][1]
        msg = email.message_from_string(raw_email.decode("utf-8"))
        msg_encoding = (
            email.header.decode_header(msg.get("Subject"))[0][1] or "iso-2022-jp"
        )
        msg_subject = email.header.decode_header(msg.get("Subject"))[0][0]
        subject = str(msg_subject.decode(msg_encoding))
        try:
            body = msg.get_payload(decode=True).decode(msg_encoding)
        except Exception as e:
            print(e)
            continue

        notion_data = {
            "parent": {"database_id": NOTION_DATABASE_ID},
            "properties": {
                "Name": {"title": [{"text": {"content": subject}}]},
            },
            "children": [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"text": {"content": body}}]},
                }
            ],
        }

        res = httpx.post(NOTION_URL, headers=HEADERS, json=notion_data)
        res.raise_for_status()

    gmail.close()
    gmail.logout()


if __name__ == "__main__":
    mail_transfer()
