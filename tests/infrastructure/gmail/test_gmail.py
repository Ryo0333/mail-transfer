from unittest.mock import MagicMock, patch

import pytest

from src.domain.models.mail import Mail
from src.infrastructure.gmail.gmail import GmailClient


def _make_msg(subject: str, from_: str, text: str = "", html: str = "") -> MagicMock:
    msg = MagicMock()
    msg.subject = subject
    msg.from_ = from_
    msg.text = text
    msg.html = html
    return msg


@pytest.fixture
def gmail_client() -> GmailClient:
    with patch("src.infrastructure.gmail.gmail.MailBox") as mock_mailbox_class:
        mock_mailbox = MagicMock()
        mock_mailbox_class.return_value.login.return_value = mock_mailbox
        return GmailClient(username="user@example.com", app_password="password", from_email="sender@example.com")


class TestToMail:
    def test_maps_subject_and_sender(self, gmail_client: GmailClient) -> None:
        msg = _make_msg("Test Subject", "from@example.com", text="Body")
        result = gmail_client._to_mail(msg)
        assert result.subject == "Test Subject"
        assert result.sender == "from@example.com"

    def test_uses_plain_text_body(self, gmail_client: GmailClient) -> None:
        msg = _make_msg("S", "f@e.com", text="Plain text", html="<p>HTML</p>")
        result = gmail_client._to_mail(msg)
        assert result.body == "Plain text"

    def test_falls_back_to_stripped_html(self, gmail_client: GmailClient) -> None:
        msg = _make_msg("S", "f@e.com", text="", html="<p>Hello</p>")
        result = gmail_client._to_mail(msg)
        assert "Hello" in result.body
        assert "<" not in result.body

    def test_empty_body_when_no_text_or_html(self, gmail_client: GmailClient) -> None:
        msg = _make_msg("S", "f@e.com", text="", html="")
        assert gmail_client._to_mail(msg).body == ""

    def test_returns_mail_instance(self, gmail_client: GmailClient) -> None:
        msg = _make_msg("S", "f@e.com", text="Body")
        assert isinstance(gmail_client._to_mail(msg), Mail)


class TestStripHtml:
    def test_strips_html_tags(self, gmail_client: GmailClient) -> None:
        result = gmail_client._strip_html("<p>Hello <b>World</b></p>")
        assert "Hello" in result
        assert "World" in result
        assert "<" not in result
        assert ">" not in result

    def test_link_text_and_href_are_preserved(self, gmail_client: GmailClient) -> None:
        result = gmail_client._strip_html('<p>詳細は<a href="https://example.com">こちら</a>へ</p>')
        assert "こちら" in result
        assert "https://example.com" in result
        assert "<a" not in result

    def test_link_url_only_is_not_duplicated(self, gmail_client: GmailClient) -> None:
        result = gmail_client._strip_html('<a href="https://example.com">https://example.com</a>')
        assert "https://example.com" in result
        assert result.count("https://example.com") == 1

    def test_link_without_href_shows_text_only(self, gmail_client: GmailClient) -> None:
        result = gmail_client._strip_html("<a>anchor text</a>")
        assert "anchor text" in result
        assert "<a" not in result


class TestFetchAll:
    def test_filters_by_subject_prefix(self, gmail_client: GmailClient) -> None:
        gmail_client.mailbox.fetch.return_value = [
            _make_msg("週刊Life is beautiful 第100号", "from@example.com", text="Body 1"),
            _make_msg("other newsletter", "from@example.com", text="Body 2"),
            _make_msg("週刊Life is beautiful 第101号", "from@example.com", text="Body 3"),
        ]
        gmail_client.subject_prefix = "週刊Life is beautiful"
        result = gmail_client.fetch_all()
        assert len(result) == 2
        assert all(mail.subject.startswith("週刊Life is beautiful") for mail in result)

    def test_no_prefix_returns_all_emails(self, gmail_client: GmailClient) -> None:
        gmail_client.mailbox.fetch.return_value = [
            _make_msg("Subject 1", "from@example.com", text="Body 1"),
            _make_msg("Subject 2", "from@example.com", text="Body 2"),
        ]
        result = gmail_client.fetch_all()
        assert len(result) == 2

    def test_returns_empty_list_when_no_emails(self, gmail_client: GmailClient) -> None:
        gmail_client.mailbox.fetch.return_value = []
        assert gmail_client.fetch_all() == []

    def test_fetches_with_from_filter(self, gmail_client: GmailClient) -> None:
        gmail_client.mailbox.fetch.return_value = [
            _make_msg("Mail 1", "sender@example.com", text="Body 1"),
            _make_msg("Mail 2", "sender@example.com", text="Body 2"),
        ]
        result = gmail_client.fetch_all()
        assert len(result) == 2
        gmail_client.mailbox.fetch.assert_called_once()
