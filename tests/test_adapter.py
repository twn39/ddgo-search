"""Unit tests for the DDGSAdapter class."""

from unittest.mock import MagicMock, patch
import pytest

from ddgs.exceptions import DDGSException, TimeoutException
from ddgo_search.adapter import DDGSAdapter
from ddgo_search.exceptions import SearchError, SearchTimeoutError


@patch("ddgo_search.adapter.DDGS")
def test_adapter_context_manager(mock_ddgs_class: MagicMock) -> None:
    """Test that context manager correctly initializes and teardowns DDGS."""
    mock_ddgs = MagicMock()
    mock_ddgs_class.return_value = mock_ddgs

    with DDGSAdapter(proxy="http://proxy", timeout=15, verify=False) as adapter:
        assert adapter.proxy == "http://proxy"
        assert adapter.timeout == 15
        assert adapter.verify is False
        mock_ddgs_class.assert_called_once_with(
            proxy="http://proxy", timeout=15, verify=False
        )
        mock_ddgs.__enter__.assert_called_once()

    mock_ddgs.__exit__.assert_called_once()


@patch("ddgo_search.adapter.DDGS")
def test_adapter_exception_mapping_on_enter(mock_ddgs_class: MagicMock) -> None:
    """Test that connection exceptions map to custom search exceptions on enter."""
    mock_ddgs = MagicMock()
    mock_ddgs.__enter__.side_effect = TimeoutException("Timeout during connect")
    mock_ddgs_class.return_value = mock_ddgs

    with pytest.raises(SearchTimeoutError) as exc_info:
        with DDGSAdapter() as _:
            pass
    assert "Connection timeout" in str(exc_info.value)


@patch("ddgo_search.adapter.DDGS")
def test_adapter_text_search(mock_ddgs_class: MagicMock) -> None:
    """Test standard text search and normalization of results."""
    mock_ddgs = MagicMock()
    mock_ddgs.text.return_value = [
        {"title": "Test Title", "href": "https://test.com/link", "body": "Test Body"}
    ]
    mock_ddgs_class.return_value = mock_ddgs

    with DDGSAdapter() as adapter:
        results = adapter.text(query="python")

        assert len(results) == 1
        assert results[0]["title"] == "Test Title"
        assert results[0]["url"] == "https://test.com/link"  # href mapped to url
        assert results[0]["body"] == "Test Body"
        mock_ddgs.text.assert_called_once_with(
            query="python",
            region="us-en",
            safesearch="moderate",
            timelimit=None,
            max_results=10,
            page=1,
            backend="auto",
        )


@patch("ddgo_search.adapter.DDGS")
def test_adapter_videos_resolution_translation(mock_ddgs_class: MagicMock) -> None:
    """Test that standard resolution translates to standart in the SDK."""
    mock_ddgs = MagicMock()
    mock_ddgs.videos.return_value = []
    mock_ddgs_class.return_value = mock_ddgs

    with DDGSAdapter() as adapter:
        adapter.videos(query="python", resolution="standard")

        mock_ddgs.videos.assert_called_once_with(
            query="python",
            region="us-en",
            safesearch="moderate",
            timelimit=None,
            max_results=10,
            page=1,
            backend="auto",
            resolution="standart",  # Translated from standard
        )


@patch("ddgo_search.adapter.DDGS")
def test_adapter_extract_format_translation(mock_ddgs_class: MagicMock) -> None:
    """Test that extract format translates markdown to text_markdown."""
    mock_ddgs = MagicMock()
    mock_ddgs.extract.return_value = {"url": "https://example.com", "content": "hello"}
    mock_ddgs_class.return_value = mock_ddgs

    with DDGSAdapter() as adapter:
        res = adapter.extract(url="https://example.com", fmt="markdown")

        assert res["content"] == "hello"
        mock_ddgs.extract.assert_called_once_with(
            url="https://example.com",
            fmt="text_markdown",  # Translated from markdown
        )


@patch("ddgo_search.adapter.DDGS")
@patch("ddgo_search.utils.scrape_ddg_lite")
def test_adapter_search_operation_exception_mapping(
    mock_scrape: MagicMock, mock_ddgs_class: MagicMock
) -> None:
    """Test that operations exceptions map to custom search exceptions when fallback also fails."""
    mock_ddgs = MagicMock()
    mock_ddgs.text.side_effect = DDGSException("Internal error")
    mock_ddgs_class.return_value = mock_ddgs
    mock_scrape.side_effect = Exception("Fallback error")

    with DDGSAdapter() as adapter:
        with pytest.raises(SearchError) as exc_info:
            adapter.text(query="fail")
        assert "Search failed on both primary and fallback engines" in str(
            exc_info.value
        )
