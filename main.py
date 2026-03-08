from application.mail_transfer_service import MailTransferService
from infrastructure.gmail import GmailClient
from infrastructure.notion import NotionClient


def main() -> None:
    with GmailClient() as gmail:
        MailTransferService(gmail=gmail, notion=NotionClient()).execute()


if __name__ == "__main__":
    main()
