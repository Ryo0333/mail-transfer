from injector import Injector

from src.usecase.mail_transfer_service import MailTransferService
from src.infrastructure.gmail.gmail import GmailClient
from src.infrastructure.gmail.provider import GmailProvider
from src.infrastructure.notion.provider import NotionProvider


def main() -> None:
    with GmailClient() as gmail:
        injector = Injector([GmailProvider(gmail), NotionProvider()])
        injector.get(MailTransferService).execute()


if __name__ == "__main__":
    main()
