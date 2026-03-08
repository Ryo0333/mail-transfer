import email
import imaplib
import os
from email.header import decode_header

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


def _parse_email(raw_bytes: bytes) -> tuple[str, str, str]:
    msg = email.message_from_bytes(raw_bytes)

    subject, encoding = decode_header(msg["Subject"])[0]
    if isinstance(subject, bytes):
        encoding = encoding if encoding else "utf-8"
        subject = subject.decode(encoding, errors="ignore")

    from_ = msg.get("From")
    if from_ is None:
        raise ValueError("From is not set")

    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            if content_type == "text/plain" and "attachment" not in content_disposition:
                try:
                    body = part.get_payload(decode=True).decode()
                    break
                except Exception as e:
                    print(f"本文のデコードに失敗しました: {e}")
    else:
        try:
            body = msg.get_payload(decode=True).decode()
        except Exception as e:
            print(f"本文のデコードに失敗しました: {e}")

    return subject, from_, body


def _post_to_notion(subject: str, body: str) -> None:
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
    email_ids = data[0].split()

    if not email_ids:
        print("No emails found")
        return

    for email_id in email_ids:
        print(f"Processing mail: {email_id}")
        status, msg_data = gmail.fetch(email_id, "(RFC822)")
        if msg_data is None:
            print(f"No email found for {email_id}")
            continue

        subject, from_, body = "", "", ""
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                subject, from_, body = _parse_email(response_part[1])
                print(f"【件名】: {subject}")
                print(f"【送信元】: {from_}")
                print(f"【本文】:\n{body}")

        _post_to_notion(subject, body)

    gmail.close()
    gmail.logout()


if __name__ == "__main__":
    mail_transfer()
