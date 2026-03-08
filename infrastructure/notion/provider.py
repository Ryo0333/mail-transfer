from injector import Module, provider

from domain.ports import MailPoster
from infrastructure.notion.notion import NotionClient


class NotionProvider(Module):
    @provider
    def mail_poster(self) -> MailPoster:
        return NotionClient()
