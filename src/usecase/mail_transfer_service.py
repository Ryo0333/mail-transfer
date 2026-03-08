from injector import inject

from src.domain.ports import MailFetcher, MailPoster
from src.logger import get_logger

logger = get_logger(__name__)


class MailTransferService:
    @inject
    def __init__(self, fetcher: MailFetcher, poster: MailPoster) -> None:
        self.fetcher = fetcher
        self.poster = poster

    def execute(self) -> None:
        mails = self.fetcher.fetch_all()
        if not mails:
            logger.info("No emails found")
            return

        for mail in mails:
            logger.info("【件名】: %s", mail.subject)
            logger.info("【送信元】: %s", mail.sender)
            logger.debug("【本文】:\n%s", mail.body)
            self.poster.post_mail(mail)
