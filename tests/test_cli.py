"""Tests for the ddgo-search Typer CLI."""

from unittest.mock import MagicMock, patch
from pathlib import Path
from typing import Generator
import pytest

from typer.testing import CliRunner

from ddgo_search.cli import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def mock_rate_limit() -> Generator[MagicMock, None, None]:
    """Mock the rate limiter sleep to speed up unit tests."""
    with patch("ddgo_search.utils.ensure_rate_limit") as mock:
        yield mock


def test_help() -> None:
    """Test that help screen outputs successfully."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "DuckDuckGo Search" in result.stdout


@patch("ddgo_search.cli.DDGS")
def test_text_command(mock_ddgs_class: MagicMock) -> None:
    """Test standard text search command."""
    mock_ddgs = MagicMock()
    mock_ddgs.text.return_value = [
        {"title": "Test Text Title", "href": "https://test.com", "body": "Test Body"}
    ]
    mock_ddgs_class.return_value.__enter__.return_value = mock_ddgs

    result = runner.invoke(app, ["text", "test query"])
    assert result.exit_code == 0
    assert "Test Text Title" in result.stdout
    mock_ddgs.text.assert_called_once_with(
        query="test query",
        region="us-en",
        safesearch="moderate",
        timelimit=None,
        max_results=10,
        page=1,
        backend="auto",
    )


@patch("ddgo_search.cli.DDGS")
def test_images_command(mock_ddgs_class: MagicMock) -> None:
    """Test images search command."""
    mock_ddgs = MagicMock()
    mock_ddgs.images.return_value = [
        {
            "title": "Test Image Title",
            "image": "https://test.com/img.jpg",
            "source": "Test Source",
            "width": 800,
            "height": 600,
        }
    ]
    mock_ddgs_class.return_value.__enter__.return_value = mock_ddgs

    result = runner.invoke(
        app,
        [
            "images",
            "test query",
            "--size",
            "Large",
            "--color",
            "red",
            "--type-image",
            "photo",
            "--layout",
            "Square",
            "--license-image",
            "any",
        ],
    )
    assert result.exit_code == 0
    assert "Test Image Title" in result.stdout
    mock_ddgs.images.assert_called_once_with(
        query="test query",
        region="us-en",
        safesearch="moderate",
        timelimit=None,
        max_results=10,
        page=1,
        backend="auto",
        size="Large",
        color="red",
        type_image="photo",
        layout="Square",
        license_image="any",
    )


@patch("ddgo_search.cli.DDGS")
def test_videos_command(mock_ddgs_class: MagicMock) -> None:
    """Test videos search command."""
    mock_ddgs = MagicMock()
    mock_ddgs.videos.return_value = [
        {
            "title": "Test Video Title",
            "duration": "10:00",
            "publisher": "YouTube",
            "published": "2026-01-01",
            "embed_url": "https://youtube.com/embed/123",
        }
    ]
    mock_ddgs_class.return_value.__enter__.return_value = mock_ddgs

    result = runner.invoke(
        app,
        [
            "videos",
            "test query",
            "--resolution",
            "high",
            "--duration",
            "short",
            "--license-videos",
            "youtube",
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0
    assert "Test Video Title" in result.stdout
    mock_ddgs.videos.assert_called_once_with(
        query="test query",
        region="us-en",
        safesearch="moderate",
        timelimit=None,
        max_results=10,
        page=1,
        backend="auto",
        resolution="high",
        duration="short",
        license_videos="youtube",
    )


@patch("ddgo_search.cli.DDGS")
def test_news_command(mock_ddgs_class: MagicMock) -> None:
    """Test news search command."""
    mock_ddgs = MagicMock()
    mock_ddgs.news.return_value = [
        {
            "date": "2026-06-03",
            "title": "Test News Title",
            "source": "CNN",
            "url": "https://cnn.com",
            "body": "News Body",
        }
    ]
    mock_ddgs_class.return_value.__enter__.return_value = mock_ddgs

    result = runner.invoke(app, ["news", "test query"])
    assert result.exit_code == 0
    assert "Test News Title" in result.stdout
    mock_ddgs.news.assert_called_once_with(
        query="test query",
        region="us-en",
        safesearch="moderate",
        timelimit=None,
        max_results=10,
        page=1,
        backend="auto",
    )


@patch("ddgo_search.cli.DDGS")
def test_books_command(mock_ddgs_class: MagicMock) -> None:
    """Test books search command."""
    mock_ddgs = MagicMock()
    mock_ddgs.books.return_value = [
        {
            "title": "Test Book Title",
            "author": "Author Name",
            "publisher": "Publisher Name",
            "info": "Book Info",
            "url": "https://test.com/book",
        }
    ]
    mock_ddgs_class.return_value.__enter__.return_value = mock_ddgs

    result = runner.invoke(app, ["books", "test query", "--format", "json"])
    assert result.exit_code == 0
    assert "Test Book Title" in result.stdout
    mock_ddgs.books.assert_called_once_with(
        query="test query",
        max_results=10,
        page=1,
        backend="auto",
    )


@patch("ddgo_search.cli.DDGS")
def test_extract_command(mock_ddgs_class: MagicMock) -> None:
    """Test extract content command."""
    mock_ddgs = MagicMock()
    mock_ddgs.extract.return_value = {
        "url": "https://example.com",
        "content": "Extracted Markdown Content",
    }
    mock_ddgs_class.return_value.__enter__.return_value = mock_ddgs

    result = runner.invoke(app, ["extract", "https://example.com"])
    assert result.exit_code == 0
    assert "Extracted Markdown Content" in result.stdout
    mock_ddgs.extract.assert_called_once_with(
        url="https://example.com",
        fmt="text_markdown",
    )


@patch("ddgo_search.cli.DDGS")
def test_extract_command_output_file(
    mock_ddgs_class: MagicMock, tmp_path: Path
) -> None:
    """Test extract command with output file path."""
    mock_ddgs = MagicMock()
    mock_ddgs.extract.return_value = {
        "url": "https://example.com",
        "content": "Extracted Markdown Content File",
    }
    mock_ddgs_class.return_value.__enter__.return_value = mock_ddgs

    out_file = tmp_path / "output.md"
    result = runner.invoke(
        app, ["extract", "https://example.com", "--output", str(out_file)]
    )
    assert result.exit_code == 0
    assert "Successfully saved content" in result.stdout
    assert out_file.read_text(encoding="utf-8") == "Extracted Markdown Content File"


def test_format_simple_table() -> None:
    """Test format_simple_table generates token-saving ASCII table correctly."""
    from ddgo_search.formatting import format_simple_table

    headers = ["Name", "Age", "City"]
    rows = [
        ["Alice", "24", "New York"],
        ["Bob", "19", "Los Angeles"],
        ["Charlie", "32", "Chicago"],
    ]
    table = format_simple_table(headers, rows)
    expected = (
        "Name      Age   City\n"
        "---------------------------\n"
        "Alice     24    New York\n"
        "Bob       19    Los Angeles\n"
        "Charlie   32    Chicago\n"
    )
    assert table == expected


@patch("httpx.Client")
def test_fetch_command_markdown(mock_client_class: MagicMock) -> None:
    """Test fetch command converting HTML to markdown."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = (
        "<html><body><h1>Hello World</h1><p>Test paragraph.</p></body></html>"
    )
    mock_response.headers = {"content-type": "text/html; charset=utf-8"}
    mock_client.get.return_value = mock_response
    mock_client_class.return_value.__enter__.return_value = mock_client

    result = runner.invoke(
        app, ["fetch", "https://example.com", "--format", "markdown"]
    )
    assert result.exit_code == 0
    assert "Hello World" in result.stdout
    assert "Test paragraph." in result.stdout


@patch("httpx.Client")
def test_fetch_command_text(mock_client_class: MagicMock) -> None:
    """Test fetch command converting HTML to clean plain text."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = (
        "<html><head><style>body {color: red;}</style></head>"
        "<body><nav>Home</nav><h1>Title</h1><p>My text</p>"
        "<script>console.log('hi');</script></body></html>"
    )
    mock_response.headers = {"content-type": "text/html"}
    mock_client.get.return_value = mock_response
    mock_client_class.return_value.__enter__.return_value = mock_client

    result = runner.invoke(app, ["fetch", "https://example.com", "--format", "text"])
    assert result.exit_code == 0
    assert "Title My text" in result.stdout
    assert "Home" not in result.stdout
    assert "console.log" not in result.stdout


@patch("httpx.Client")
def test_fetch_command_html(mock_client_class: MagicMock) -> None:
    """Test fetch command returning body HTML."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "<html><body><h1>Hello World</h1></body></html>"
    mock_response.headers = {"content-type": "text/html"}
    mock_client.get.return_value = mock_response
    mock_client_class.return_value.__enter__.return_value = mock_client

    result = runner.invoke(app, ["fetch", "https://example.com", "--format", "html"])
    assert result.exit_code == 0
    assert "<html>" in result.stdout
    assert "<body>" in result.stdout
    assert "<h1>Hello World</h1>" in result.stdout


@patch("httpx.Client")
def test_fetch_command_truncation(mock_client_class: MagicMock) -> None:
    """Test fetch command correctly truncating output when it exceeds max size."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "A" * 200
    mock_response.headers = {"content-type": "text/plain"}
    mock_client.get.return_value = mock_response
    mock_client_class.return_value.__enter__.return_value = mock_client

    result = runner.invoke(
        app, ["fetch", "https://example.com", "--format", "text", "--max-size", "50"]
    )
    assert result.exit_code == 0
    assert "Content truncated to 50 bytes" in result.stdout
    assert len(result.stdout.split("\n")[0]) == 50


def test_run_action_success() -> None:
    """Test _run_action succeeds when the action function returns successfully."""
    from ddgo_search.cli import _run_action, Config

    mock_ctx = MagicMock()
    mock_ctx.obj = Config(proxy=None, timeout=10, verify=True, max_retries=1)

    dummy_func = MagicMock(return_value="success_result")

    res = _run_action(mock_ctx, dummy_func)
    assert res == "success_result"
    dummy_func.assert_called_once_with(None)


def test_run_action_exception() -> None:
    """Test _run_action exits with code 1 when the action function raises an exception."""
    from ddgo_search.cli import _run_action, Config
    import typer

    mock_ctx = MagicMock()
    mock_ctx.obj = Config(proxy=None, timeout=10, verify=True, max_retries=1)

    dummy_func = MagicMock(side_effect=ValueError("Test Network Error"))

    with pytest.raises(typer.Exit) as exc_info:
        _run_action(mock_ctx, dummy_func)
    assert exc_info.value.exit_code == 1


@patch("ddgo_search.cli.DDGS")
@patch("ddgo_search.cli.display_results")
def test_run_ddgs_search_dynamic_dispatch(
    mock_display: MagicMock, mock_ddgs_class: MagicMock
) -> None:
    """Test _run_ddgs_search resolves method via reflection and processes results."""
    from ddgo_search.cli import _run_ddgs_search, Config

    mock_ctx = MagicMock()
    mock_ctx.obj = Config(proxy=None, timeout=10, verify=True, max_retries=1)

    mock_ddgs = MagicMock()
    mock_ddgs.text.return_value = [{"title": "Dynamic Text"}]
    mock_ddgs_class.return_value.__enter__.return_value = mock_ddgs

    # Run text query dynamically via reflection
    _run_ddgs_search(
        mock_ctx,
        method_name="text",
        category="text",
        fmt="json",
        query="dynamic query",
    )

    # Assert correct method was resolved and called
    mock_ddgs.text.assert_called_once_with(query="dynamic query")
    # Assert display_results was called with results
    mock_display.assert_called_once_with([{"title": "Dynamic Text"}], "text", "json")


@patch("ddgo_search.cli.DDGS")
def test_run_ddgs_search_method_not_found(mock_ddgs_class: MagicMock) -> None:
    """Test _run_ddgs_search exits with code 1 when method_name does not exist on DDGS."""
    from ddgo_search.cli import _run_ddgs_search, Config
    from ddgs import DDGS
    import typer

    mock_ctx = MagicMock()
    mock_ctx.obj = Config(proxy=None, timeout=10, verify=True, max_retries=1)

    mock_ddgs = MagicMock(spec=DDGS)
    mock_ddgs_class.return_value.__enter__.return_value = mock_ddgs

    with pytest.raises(typer.Exit) as exc_info:
        _run_ddgs_search(
            mock_ctx,
            method_name="nonexistent",
            category="text",
            fmt="json",
            query="test",
        )
    assert exc_info.value.exit_code == 1
