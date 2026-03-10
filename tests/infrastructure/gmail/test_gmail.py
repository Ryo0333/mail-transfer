import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from unittest.mock import MagicMock, patch

import pytest

from src.domain.models.mail import Mail
from src.infrastructure.gmail.gmail import GmailClient


@pytest.fixture
def gmail_client() -> GmailClient:
    with patch("src.infrastructure.gmail.gmail.imaplib.IMAP4_SSL") as mock_imap_class:
        mock_imap = MagicMock()
        mock_imap_class.return_value = mock_imap
        client = GmailClient(username="user@example.com", app_password="password", from_email="sender@example.com")
        return client


class TestParseEmail:
    def test_simple_plain_text(self, gmail_client: GmailClient) -> None:
        # Arrange
        msg = email.message.EmailMessage()
        msg["Subject"] = "Test Subject"
        msg["From"] = "sender@example.com"
        msg.set_content("Hello World")

        # Act
        result = gmail_client._parse_email(msg.as_bytes())

        # Assert
        assert result.subject == "Test Subject"
        assert result.sender == "sender@example.com"
        assert "Hello World" in result.body

    def test_multipart_uses_plain_text_part(self, gmail_client: GmailClient) -> None:
        # Arrange
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Multipart Subject"
        msg["From"] = "multipart@example.com"
        msg.attach(MIMEText("Plain text body", "plain"))
        msg.attach(MIMEText("<html>HTML body</html>", "html"))

        # Act
        result = gmail_client._parse_email(msg.as_bytes())

        # Assert
        assert result.subject == "Multipart Subject"
        assert result.sender == "multipart@example.com"
        assert "Plain text body" in result.body

    def test_encoded_utf8_subject(self, gmail_client: GmailClient) -> None:
        # Arrange ("テスト" encoded as UTF-8 base64)
        msg = MIMEMultipart()
        msg["Subject"] = "=?utf-8?b?44OG44K544OI?="
        msg["From"] = "sender@example.com"
        msg.attach(MIMEText("Body", "plain"))

        # Act
        result = gmail_client._parse_email(msg.as_bytes())

        # Assert
        assert result.subject == "テスト"
        assert result.sender == "sender@example.com"

    def test_raises_when_from_header_missing(self, gmail_client: GmailClient) -> None:
        # Arrange
        msg = email.message.EmailMessage()
        msg["Subject"] = "No Sender"
        msg.set_content("Body")

        # Act & Assert
        with pytest.raises(ValueError, match="From is not set"):
            gmail_client._parse_email(msg.as_bytes())

    def test_returns_mail_instance(self, gmail_client: GmailClient) -> None:
        # Arrange
        msg = email.message.EmailMessage()
        msg["Subject"] = "Subject"
        msg["From"] = "from@example.com"
        msg.set_content("Body")

        # Act
        result = gmail_client._parse_email(msg.as_bytes())

        # Assert
        assert isinstance(result, Mail)

    def test_empty_body(self, gmail_client: GmailClient) -> None:
        # Arrange
        msg = MIMEMultipart()
        msg["Subject"] = "Empty Body"
        msg["From"] = "sender@example.com"
        msg.attach(MIMEText("", "plain"))

        # Act
        result = gmail_client._parse_email(msg.as_bytes())

        # Assert
        assert result.body == ""

    def test_iso2022jp_body_is_decoded_correctly(self, gmail_client: GmailClient) -> None:
        # Arrange
        msg = MIMEMultipart()
        msg["Subject"] = "ISO-2022-JP test"
        msg["From"] = "sender@example.com"
        msg.attach(MIMEText("日本語の本文", "plain", "iso-2022-jp"))

        # Act
        result = gmail_client._parse_email(msg.as_bytes())

        # Assert
        assert result.body == "日本語の本文"

    def test_iso2022jp_body_multipart_is_decoded_correctly(self, gmail_client: GmailClient) -> None:
        # Arrange
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "ISO-2022-JP multipart test"
        msg["From"] = "sender@example.com"
        msg.attach(MIMEText("日本語の本文", "plain", "iso-2022-jp"))
        msg.attach(MIMEText("<p>日本語</p>", "html", "iso-2022-jp"))

        # Act
        result = gmail_client._parse_email(msg.as_bytes())

        # Assert
        assert result.body == "日本語の本文"


class TestFetchAll:
    def test_filters_by_subject_prefix(self) -> None:
        # Arrange
        with patch("src.infrastructure.gmail.gmail.imaplib.IMAP4_SSL") as mock_imap_class:
            mock_imap = MagicMock()
            mock_imap_class.return_value = mock_imap
            client = GmailClient(
                username="user@example.com",
                app_password="password",
                from_email="sender@example.com",
                subject_prefix="週刊Life is beautiful",
            )

        client.client = mock_imap
        client.client.search.return_value = (None, [b"1 2 3"])

        def fake_fetch(email_id: str, fmt: str) -> tuple[None, list]:
            subjects = {"1": "週刊Life is beautiful 第100号", "2": "other newsletter", "3": "週刊Life is beautiful 第101号"}
            msg = email.message.EmailMessage()
            msg["Subject"] = subjects[email_id]
            msg["From"] = "from@example.com"
            msg.set_content(f"Body {email_id}")
            return (None, [(None, msg.as_bytes())])

        client.client.fetch.side_effect = fake_fetch

        # Act
        result = client.fetch_all()

        # Assert
        assert len(result) == 2
        assert all(mail.subject.startswith("週刊Life is beautiful") for mail in result)

    def test_no_prefix_returns_all_emails(self, gmail_client: GmailClient) -> None:
        # Arrange
        gmail_client.client.search.return_value = (None, [b"1 2"])

        def fake_fetch(email_id: str, fmt: str) -> tuple[None, list]:
            subjects = {"1": "週刊Life is beautiful 第100号", "2": "other newsletter"}
            msg = email.message.EmailMessage()
            msg["Subject"] = subjects[email_id]
            msg["From"] = "from@example.com"
            msg.set_content(f"Body {email_id}")
            return (None, [(None, msg.as_bytes())])

        gmail_client.client.fetch.side_effect = fake_fetch

        # Act
        result = gmail_client.fetch_all()

        # Assert
        assert len(result) == 2

    def test_returns_empty_list_when_no_emails(self, gmail_client: GmailClient) -> None:
        # Arrange
        gmail_client.client.search.return_value = (None, [b""])

        # Act
        result = gmail_client.fetch_all()

        # Assert
        assert result == []
        gmail_client.client.search.assert_called_once_with(None, 'FROM "sender@example.com"')

    def test_fetches_each_email_by_id(self, gmail_client: GmailClient) -> None:
        # Arrange
        gmail_client.client.search.return_value = (None, [b"1 2"])

        def fake_fetch(email_id: str, fmt: str) -> tuple[None, list]:
            msg = email.message.EmailMessage()
            msg["Subject"] = f"Mail {email_id}"
            msg["From"] = "from@example.com"
            msg.set_content(f"Body {email_id}")
            return (None, [(None, msg.as_bytes())])

        gmail_client.client.fetch.side_effect = fake_fetch

        # Act
        result = gmail_client.fetch_all()

        # Assert
        assert len(result) == 2
        assert gmail_client.client.fetch.call_count == 2


class TestFetchById:
    def test_raises_when_no_matching_response(self, gmail_client: GmailClient) -> None:
        # Arrange
        gmail_client.client.fetch.return_value = (None, [None])

        # Act & Assert
        with pytest.raises(ValueError, match="No email found for 42"):
            gmail_client._fetch_by_id("42")
