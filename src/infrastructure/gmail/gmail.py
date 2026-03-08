import email
import imaplib
from email.header import decode_header

from src.domain.models.mail import Mail
from src.core.settings import settings

IMAP_SERVER = "imap.gmail.com"


class GmailClient:
    def __init__(self) -> None:
        self._client = imaplib.IMAP4_SSL(IMAP_SERVER)
        self._client.login(settings.gmail_username, settings.gmail_app_password)
        self._client.select("inbox")

    def fetch_all(self) -> list[Mail]:
        _, data = self._client.search(None, f"FROM {settings.from_email}")
        # _, data = self._client.search(None, "ALL")
        email_ids = data[0].split()
        if not email_ids:
            return []
        return [self._fetch_one(email_id.decode()) for email_id in email_ids]

    def _fetch_one(self, email_id: str) -> Mail:
        _, msg_data = self._client.fetch(email_id, "(RFC822)")
        for response_part in msg_data or []:
            if isinstance(response_part, tuple):
                return self._parse_email(response_part[1])
        raise ValueError(f"No email found for {email_id}")

    def __enter__(self) -> "GmailClient":
        return self

    def __exit__(self, *_: object) -> None:
        self._client.close()
        self._client.logout()

    def _parse_email(self, raw_bytes: bytes) -> Mail:
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
                        payload = part.get_payload(decode=True)
                        body = payload.decode() if isinstance(payload, bytes) else ""
                        break
                    except Exception as e:
                        print(f"本文のデコードに失敗しました: {e}")
        else:
            try:
                payload = msg.get_payload(decode=True)
                body = payload.decode() if isinstance(payload, bytes) else ""
            except Exception as e:
                print(f"本文のデコードに失敗しました: {e}")

        return Mail(subject=subject, from_=from_, body=body)
