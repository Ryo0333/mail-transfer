from injector import Module, provider

from src.domain.ports import MailFetcher
from src.infrastructure.gmail.gmail import GmailClient


class GmailProvider(Module):
    def __init__(self, gmail: GmailClient) -> None:
        self._gmail = gmail

    @provider
    def mail_fetcher(self) -> MailFetcher:
        return self._gmail
