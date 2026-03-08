from injector import inject

from src.domain.ports import MailFetcher, MailPoster


class MailTransferService:
    @inject
    def __init__(self, gmail: MailFetcher, notion: MailPoster) -> None:
        self.gmail = gmail
        self.notion = notion

    def execute(self) -> None:
        mails = self.gmail.fetch_all()
        if not mails:
            print("No emails found")
            return

        for mail in mails:
            print(f"【件名】: {mail.subject}")
            print(f"【送信元】: {mail.sender}")
            print(f"【本文】:\n{mail.body}")
            self.notion.post_mail(mail)
