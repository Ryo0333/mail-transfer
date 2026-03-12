from bs4 import BeautifulSoup
from imap_tools import AND, MailBox, MailMessage

from src.domain.models.mail import Mail
from src.logger import get_logger

logger = get_logger(__name__)

IMAP_SERVER = "imap.gmail.com"


class GmailClient:
    def __init__(self, username: str, app_password: str, from_email: str, subject_prefix: str | None = None) -> None:
        self.from_email = from_email
        self.subject_prefix = subject_prefix
        self.mailbox = MailBox(IMAP_SERVER).login(username, app_password)

    def __enter__(self) -> "GmailClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.mailbox.logout()

    def fetch_all(self) -> list[Mail]:
        messages = self.mailbox.fetch(AND(from_=self.from_email))
        return [
            self._to_mail(msg)
            for msg in messages
            if self.subject_prefix is None or msg.subject.startswith(self.subject_prefix)
        ]

    def _to_mail(self, msg: MailMessage) -> Mail:
        return Mail(
            subject=msg.subject,
            sender=msg.from_,
            body=msg.text or (self._strip_html(msg.html) if msg.html else ""),
        )

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
