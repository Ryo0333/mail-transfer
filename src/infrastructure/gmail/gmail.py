import email
import imaplib
from email.header import decode_header
from email.message import Message

from bs4 import BeautifulSoup

from src.domain.models.mail import Mail
from src.logger import get_logger

logger = get_logger(__name__)

IMAP_SERVER = "imap.gmail.com"


class GmailClient:
    def __init__(self, username: str, app_password: str, from_email: str, subject_prefix: str | None = None) -> None:
        self.from_email = from_email
        self.subject_prefix = subject_prefix
        self.client = imaplib.IMAP4_SSL(IMAP_SERVER)
        self.client.login(username, app_password)
        self.client.select("inbox")

    def __enter__(self) -> "GmailClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.client.close()
        self.client.logout()

    def fetch_all(self) -> list[Mail]:
        _, data = self.client.search(None, f'FROM "{self.from_email}"')
        email_ids: list[bytes] = data[0].split()

        mails = [self._fetch_by_id(email_id.decode()) for email_id in email_ids]
        if self.subject_prefix is not None:
            mails = [mail for mail in mails if mail.subject.startswith(self.subject_prefix)]
        return mails

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
        subject = self._decode_subject(msg["Subject"])
        sender = msg.get("From")
        if sender is None:
            raise ValueError("From is not set")
        return Mail(subject=subject, sender=sender, body=self._extract_body(msg))

    def _decode_subject(self, raw_subject: str) -> str:
        subject, encoding = decode_header(raw_subject)[0]
        if isinstance(subject, bytes):
            return subject.decode(encoding if encoding else "utf-8")
        return subject

    def _extract_body(self, msg: Message) -> str:
        if msg.is_multipart():
            return self._extract_body_multipart(msg)
        return self._extract_body_single(msg)

    def _extract_body_multipart(self, msg: Message) -> str:
        html_fallback: str | None = None
        for part in msg.walk():
            content_type = part.get_content_type()
            if "attachment" in str(part.get("Content-Disposition")):
                continue
            try:
                payload = part.get_payload(decode=True)
                if not isinstance(payload, bytes):
                    continue
                text = payload.decode(part.get_content_charset() or "iso-2022-jp")
                if content_type == "text/plain":
                    return text
                if content_type == "text/html" and html_fallback is None:
                    html_fallback = text
            except Exception as e:
                logger.warning("本文のデコードに失敗しました: %s", e)
        return self._strip_html(html_fallback) if html_fallback else ""

    def _extract_body_single(self, msg: Message) -> str:
        try:
            payload = msg.get_payload(decode=True)
            if not isinstance(payload, bytes):
                return ""
            text = payload.decode(msg.get_content_charset() or "iso-2022-jp")
            return self._strip_html(text) if msg.get_content_type() == "text/html" else text
        except Exception as e:
            logger.warning("本文のデコードに失敗しました: %s", e)
            return ""

    def _strip_html(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a"):
            href = a.get("href")
            text = a.get_text(strip=True)
            if not href:
                a.replace_with(text)
                continue
            if text != href:
                a.replace_with(f"{text} ({href})")
                continue
            a.replace_with(str(href))
        return soup.get_text(separator="\n")
