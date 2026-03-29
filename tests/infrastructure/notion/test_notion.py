from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.domain.models.mail import Mail
from src.infrastructure.notion.notion import NOTION_RICH_TEXT_LIMIT, NotionClient


@pytest.fixture
def notion_client() -> NotionClient:
    return NotionClient(api_key="test-api-key", data_source_id="test-db-id")


def _make_mock_http_client(is_success: bool = True, json_data: dict[str, Any] | None = None) -> MagicMock:
    mock_response = MagicMock()
    mock_response.is_success = is_success
    mock_response.json.return_value = json_data or {}

    mock_client = MagicMock()
    mock_client.post.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    return mock_client


class TestSplitIntoParagraphBlocks:
    def test_empty_text_returns_empty_list(self, notion_client: NotionClient) -> None:
        # Act
        result = notion_client._split_into_paragraph_blocks("")

        # Assert
        assert result == []

    def test_short_text_returns_single_block(self, notion_client: NotionClient) -> None:
        # Arrange
        text = "Hello, World!"

        # Act
        result = notion_client._split_into_paragraph_blocks(text)

        # Assert
        assert len(result) == 1
        assert result[0]["object"] == "block"
        assert result[0]["type"] == "paragraph"
        assert result[0]["paragraph"]["rich_text"][0]["text"]["content"] == text

    def test_text_at_exact_limit_returns_single_block(self, notion_client: NotionClient) -> None:
        # Arrange
        text = "A" * NOTION_RICH_TEXT_LIMIT

        # Act
        result = notion_client._split_into_paragraph_blocks(text)

        # Assert
        assert len(result) == 1

    def test_long_text_splits_into_multiple_blocks(self, notion_client: NotionClient) -> None:
        # Arrange
        text = "A" * (NOTION_RICH_TEXT_LIMIT * 2 + 500)

        # Act
        result = notion_client._split_into_paragraph_blocks(text)

        # Assert
        assert len(result) == 3
        assert len(result[0]["paragraph"]["rich_text"][0]["text"]["content"]) == NOTION_RICH_TEXT_LIMIT
        assert len(result[1]["paragraph"]["rich_text"][0]["text"]["content"]) == NOTION_RICH_TEXT_LIMIT
        assert len(result[2]["paragraph"]["rich_text"][0]["text"]["content"]) == 500

    def test_each_block_has_correct_structure(self, notion_client: NotionClient) -> None:
        # Act
        result = notion_client._split_into_paragraph_blocks("test")

        # Assert
        block = result[0]
        assert "object" in block
        assert "type" in block
        assert "paragraph" in block
        assert "rich_text" in block["paragraph"]
        assert "text" in block["paragraph"]["rich_text"][0]
        assert "content" in block["paragraph"]["rich_text"][0]["text"]

    def test_concatenated_blocks_reconstruct_original_text(self, notion_client: NotionClient) -> None:
        # Arrange
        text = "X" * (NOTION_RICH_TEXT_LIMIT + 300)

        # Act
        result = notion_client._split_into_paragraph_blocks(text)

        # Assert
        reconstructed = "".join(b["paragraph"]["rich_text"][0]["text"]["content"] for b in result)
        assert reconstructed == text


class TestMessageIdExists:
    def test_returns_true_when_results_present(self, notion_client: NotionClient) -> None:
        # Arrange
        mock_client = _make_mock_http_client(json_data={"results": [{"id": "page-id"}]})

        # Act
        with patch("src.infrastructure.notion.notion.httpx.Client", return_value=mock_client):
            result = notion_client._message_id_exists("<abc@example.com>")

        # Assert
        assert result is True

    def test_returns_false_when_results_empty(self, notion_client: NotionClient) -> None:
        # Arrange
        mock_client = _make_mock_http_client(json_data={"results": []})

        # Act
        with patch("src.infrastructure.notion.notion.httpx.Client", return_value=mock_client):
            result = notion_client._message_id_exists("<xyz@example.com>")

        # Assert
        assert result is False

    def test_raises_on_api_error(self, notion_client: NotionClient) -> None:
        # Arrange
        mock_client = _make_mock_http_client(is_success=False)
        mock_client.post.return_value.raise_for_status.side_effect = Exception("API Error")

        # Act & Assert
        with patch("src.infrastructure.notion.notion.httpx.Client", return_value=mock_client):
            with pytest.raises(Exception, match="API Error"):
                notion_client._message_id_exists("<abc@example.com>")


mail = Mail(message_id="<test@example.com>", subject="Existing Subject", sender="sender@example.com", body="Body")


class TestExport:
    def test_skips_export_when_message_id_exists(self, notion_client: NotionClient) -> None:
        # Arrange
        mock_client = _make_mock_http_client()

        # Act
        with patch.object(notion_client, "_message_id_exists", return_value=True) as mock_exists:
            with patch("src.infrastructure.notion.notion.httpx.Client", return_value=mock_client):
                notion_client.export(mail)

        # Assert
        mock_exists.assert_called_once_with(mail.message_id)
        mock_client.post.assert_not_called()

    def test_posts_to_notion_when_message_id_not_exists(self, notion_client: NotionClient) -> None:
        # Arrange
        mock_client = _make_mock_http_client()

        # Act
        with patch.object(notion_client, "_message_id_exists", return_value=False):
            with patch("src.infrastructure.notion.notion.httpx.Client", return_value=mock_client):
                notion_client.export(mail)

        # Assert
        mock_client.post.assert_called_once()

    def test_raises_on_failed_export(self, notion_client: NotionClient) -> None:
        # Arrange
        mock_client = _make_mock_http_client(is_success=False)
        mock_client.post.return_value.raise_for_status.side_effect = Exception("Export Failed")

        # Act & Assert
        with patch.object(notion_client, "_message_id_exists", return_value=False):
            with patch("src.infrastructure.notion.notion.httpx.Client", return_value=mock_client):
                with pytest.raises(Exception, match="Export Failed"):
                    notion_client.export(mail)

    def test_export_includes_subject_as_title(self, notion_client: NotionClient) -> None:
        # Arrange
        _mail = Mail(
            message_id="<title@example.com>", subject="My Title", sender="sender@example.com", body="Body content"
        )
        mock_client = _make_mock_http_client()

        # Act
        with patch.object(notion_client, "_message_id_exists", return_value=False):
            with patch("src.infrastructure.notion.notion.httpx.Client", return_value=mock_client):
                notion_client.export(_mail)

        # Assert
        call_kwargs = mock_client.post.call_args
        payload = (
            call_kwargs.kwargs.get("json") or call_kwargs.args[1]
            if len(call_kwargs.args) > 1
            else call_kwargs.kwargs["json"]
        )
        title_content = payload["properties"]["Name"]["title"][0]["text"]["content"]
        assert title_content == "My Title"

    def test_export_includes_message_id_property(self, notion_client: NotionClient) -> None:
        # Arrange
        _mail = Mail(message_id="<mid@example.com>", subject="Subject", sender="sender@example.com", body="Body")
        mock_client = _make_mock_http_client()

        # Act
        with patch.object(notion_client, "_message_id_exists", return_value=False):
            with patch("src.infrastructure.notion.notion.httpx.Client", return_value=mock_client):
                notion_client.export(_mail)

        # Assert
        call_kwargs = mock_client.post.call_args
        payload = (
            call_kwargs.kwargs.get("json") or call_kwargs.args[1]
            if len(call_kwargs.args) > 1
            else call_kwargs.kwargs["json"]
        )
        message_id_content = payload["properties"]["Message ID"]["rich_text"][0]["text"]["content"]
        assert message_id_content == "<mid@example.com>"
