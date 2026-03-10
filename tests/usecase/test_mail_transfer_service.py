from unittest.mock import MagicMock

from src.domain.models.mail import Mail
from src.usecase.mail_transfer_service import MailTransferService


def _make_service(mails: list[Mail]) -> tuple[MailTransferService, MagicMock, MagicMock]:
    fetcher = MagicMock()
    fetcher.fetch_all.return_value = mails
    exporter = MagicMock()
    service = MailTransferService(fetcher=fetcher, exporter=exporter)
    return service, fetcher, exporter


def test_execute_calls_fetch_all() -> None:
    # Arrange
    service, fetcher, _ = _make_service([])

    # Act
    service.execute()

    # Assert
    fetcher.fetch_all.assert_called_once()


def test_execute_no_mails_skips_export() -> None:
    # Arrange
    service, _, exporter = _make_service([])

    # Act
    service.execute()

    # Assert
    exporter.export.assert_not_called()


def test_execute_single_mail_exports_once() -> None:
    # Arrange
    mail = Mail(subject="Subject", sender="sender@example.com", body="Body")
    service, _, exporter = _make_service([mail])

    # Act
    service.execute()

    # Assert
    exporter.export.assert_called_once_with(mail)


def test_execute_multiple_mails_exports_all() -> None:
    # Arrange
    mails = [
        Mail(subject="Subject 1", sender="a@example.com", body="Body 1"),
        Mail(subject="Subject 2", sender="b@example.com", body="Body 2"),
        Mail(subject="Subject 3", sender="c@example.com", body="Body 3"),
    ]
    service, _, exporter = _make_service(mails)

    # Act
    service.execute()

    # Assert
    assert exporter.export.call_count == 3
    for mail in mails:
        exporter.export.assert_any_call(mail)


def test_execute_preserves_mail_order() -> None:
    # Arrange
    mails = [
        Mail(subject="First", sender="a@example.com", body=""),
        Mail(subject="Second", sender="b@example.com", body=""),
    ]
    service, _, exporter = _make_service(mails)

    # Act
    service.execute()

    # Assert
    call_args = [call.args[0] for call in exporter.export.call_args_list]
    assert call_args == mails
