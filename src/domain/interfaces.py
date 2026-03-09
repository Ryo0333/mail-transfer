from typing import Protocol

from src.domain.models.mail import Mail


class MailFetcher(Protocol):
    def fetch_all(self) -> list[Mail]: ...


class MailExporter(Protocol):
    def export(self, mail: Mail) -> None: ...
