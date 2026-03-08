from injector import Injector

from application.mail_transfer_service import MailTransferService
from infrastructure.gmail.gmail import GmailClient
from infrastructure.gmail.provider import GmailProvider
from infrastructure.notion.provider import NotionProvider


def main() -> None:
    with GmailClient() as gmail:
        injector = Injector([GmailProvider(gmail), NotionProvider()])
        injector.get(MailTransferService).execute()


if __name__ == "__main__":
    main()
