from injector import inject

from src.domain.interfaces import MailExporter, MailFetcher
from src.logger import get_logger

logger = get_logger(__name__)


class MailTransferService:
    @inject
    def __init__(self, fetcher: MailFetcher, exporter: MailExporter) -> None:
        self.fetcher = fetcher
        self.exporter = exporter

    def execute(self) -> None:
        mails = self.fetcher.fetch_all()
        if not mails:
            logger.info("No emails found")
            return

        for mail in mails:
            logger.info("【件名】: %s", mail.subject)
            logger.info("【送信元】: %s", mail.sender)
            logger.debug("【本文】:\n%s", mail.body)
            self.exporter.export(mail)
