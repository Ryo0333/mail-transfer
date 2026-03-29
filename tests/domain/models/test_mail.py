import pytest
from pydantic import ValidationError

from src.domain.models.mail import Mail


def test_mail_creation() -> None:
    # Act
    mail = Mail(message_id="<test@example.com>", subject="Test Subject", sender="test@example.com", body="Test body")

    # Assert
    assert mail.message_id == "<test@example.com>"
    assert mail.subject == "Test Subject"
    assert mail.sender == "test@example.com"
    assert mail.body == "Test body"


def test_mail_empty_fields() -> None:
    # Act
    mail = Mail(message_id="", subject="", sender="", body="")

    # Assert
    assert mail.subject == ""
    assert mail.sender == ""
    assert mail.body == ""


def test_mail_strict_str_rejects_int_subject() -> None:
    # Act & Assert
    with pytest.raises(ValidationError):
        Mail(message_id="<id>", subject=123, sender="sender@example.com", body="body")  # type: ignore[arg-type]


def test_mail_strict_str_rejects_int_sender() -> None:
    # Act & Assert
    with pytest.raises(ValidationError):
        Mail(message_id="<id>", subject="subject", sender=456, body="body")  # type: ignore[arg-type]


def test_mail_strict_str_rejects_int_body() -> None:
    # Act & Assert
    with pytest.raises(ValidationError):
        Mail(message_id="<id>", subject="subject", sender="sender@example.com", body=789)  # type: ignore[arg-type]


def test_mail_strict_str_rejects_none() -> None:
    # Act & Assert
    with pytest.raises(ValidationError):
        Mail(message_id="<id>", subject=None, sender="sender@example.com", body="body")  # type: ignore[arg-type]


def test_mail_multiline_body() -> None:
    # Arrange
    body = "Line 1\nLine 2\nLine 3"

    # Act
    mail = Mail(message_id="<id>", subject="Subject", sender="sender@example.com", body=body)

    # Assert
    assert mail.body == body
