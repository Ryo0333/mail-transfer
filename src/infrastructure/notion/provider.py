from injector import Module, provider

from src.domain.ports import MailPoster
from src.infrastructure.notion.notion import NotionClient


class NotionProvider(Module):
    @provider
    def mail_poster(self) -> MailPoster:
        return NotionClient()
