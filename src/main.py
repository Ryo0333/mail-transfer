from injector import Injector

from src.infrastructure.gmail.gmail import GmailClient
from src.infrastructure.gmail.provider import GmailProvider
from src.infrastructure.notion.provider import NotionProvider
from src.settings import settings
from src.usecase.mail_transfer_service import MailTransferService


def main() -> None:
    gmail_client = GmailClient(
        username=settings.gmail_username,
        app_password=settings.gmail_app_password,
        from_email=settings.from_email,
        subject_prefix=settings.subject_prefix,
    )
    notion_provider = NotionProvider(
        api_key=settings.notion_api_key,
        data_source_id=settings.notion_data_source_id,
    )
    with gmail_client as gmail:
        injector = Injector([GmailProvider(gmail), notion_provider])
        injector.get(MailTransferService).execute()


if __name__ == "__main__":
    main()
