from injector import Module, provider

from src.domain.interfaces import MailExporter
from src.infrastructure.notion.notion import NotionClient


class NotionProvider(Module):
    @provider
    def mail_exporter(self) -> MailExporter:
        return NotionClient()
