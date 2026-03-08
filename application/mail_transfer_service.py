from infrastructure.gmail import GmailClient
from infrastructure.notion import NotionClient


class MailTransferService:
    def __init__(self, gmail: GmailClient, notion: NotionClient) -> None:
        self._gmail = gmail
        self._notion = notion

    def execute(self) -> None:
        mails = self._gmail.fetch_all()
        if not mails:
            print("No emails found")
            return

        for mail in mails:
            print(f"【件名】: {mail.subject}")
            print(f"【送信元】: {mail.from_}")
            print(f"【本文】:\n{mail.body}")
            self._notion.post_mail(mail)
