from injector import Module, provider

from src.domain.interfaces import MailExporter
from src.infrastructure.notion.notion import NotionClient


class NotionProvider(Module):
    def __init__(self, api_key: str, data_source_id: str) -> None:
        self.api_key = api_key
        self.data_source_id = data_source_id

    @provider
    def mail_exporter(self) -> MailExporter:
        return NotionClient(self.api_key, self.data_source_id)
