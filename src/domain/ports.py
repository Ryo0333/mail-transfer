from typing import Protocol

from src.domain.models.mail import Mail


class MailFetcher(Protocol):
    def fetch_all(self) -> list[Mail]: ...


class MailPoster(Protocol):
    def post_mail(self, mail: Mail) -> None: ...
