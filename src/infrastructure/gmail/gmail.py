import email
import imaplib
from email.header import decode_header

from src.domain.models.mail import Mail
from src.logger import get_logger
from src.settings import settings

logger = get_logger(__name__)

IMAP_SERVER = "imap.gmail.com"


class GmailClient:
    def __init__(self) -> None:
        self.client = imaplib.IMAP4_SSL(IMAP_SERVER)
        self.client.login(settings.gmail_username, settings.gmail_app_password)
        self.client.select("inbox")

    def __enter__(self) -> "GmailClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.client.close()
        self.client.logout()

    def fetch_all(self) -> list[Mail]:
        _, data = self.client.search(None, f"FROM {settings.from_email}")
        # _, data = self._client.search(None, "ALL")
        email_ids: list[bytes] = data[0].split()

        return [self._fetch_by_id(email_id.decode()) for email_id in email_ids]

    def _fetch_by_id(self, email_id: str) -> Mail:
        _, msg_data = self.client.fetch(email_id, "(RFC822)")
        for response_part in msg_data:
            if response_part is None:
                continue
            if isinstance(response_part, tuple):
                return self._parse_email(response_part[1])
        raise ValueError(f"No email found for {email_id}")

    def _parse_email(self, raw_bytes: bytes) -> Mail:
        msg = email.message_from_bytes(raw_bytes)

        subject, encoding = decode_header(msg["Subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding if encoding else "utf-8")

        sender = msg.get("From")
        if sender is None:
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
                        logger.warning("本文のデコードに失敗しました: %s", e)
        else:
            try:
                payload = msg.get_payload(decode=True)
                body = payload.decode() if isinstance(payload, bytes) else ""
            except Exception as e:
                logger.warning("本文のデコードに失敗しました: %s", e)

        return Mail(subject=subject, sender=sender, body=body)
