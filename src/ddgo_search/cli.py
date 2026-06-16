"""Main Typer CLI application for ddgo-search."""

from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

import typer
from ddgs import DDGS
from rich.console import Console

from .formatting import display_results
from .utils import (
    clean_markdown,
    execute_with_retry,
    fetch_url,
    parse_proxies,
)

app = typer.Typer(
    name="ddgo-search",
    help="DuckDuckGo Search (ddgo) Command Line Interface wrapper.",
    no_args_is_help=True,
)

console = Console()
err_console = Console(stderr=True)


class OutputFormat(str, Enum):
    """Supported output formats for search results."""

    TABLE = "table"
    JSON = "json"
    CSV = "csv"
    PLAIN = "plain"


class SafeSearch(str, Enum):
    """SafeSearch options."""

    ON = "on"
    MODERATE = "moderate"
    OFF = "off"


class ImageSize(str, Enum):
    """Image size options."""

    SMALL = "Small"
    MEDIUM = "Medium"
    LARGE = "Large"
    WALLPAPER = "Wallpaper"


class ImageType(str, Enum):
    """Image type options."""

    PHOTO = "photo"
    CLIPART = "clipart"
    GIF = "gif"
    TRANSPARENT = "transparent"
    LINE = "line"


class ImageLayout(str, Enum):
    """Image layout options."""

    SQUARE = "Square"
    TALL = "Tall"
    WIDE = "Wide"


class VideoResolution(str, Enum):
    """Video resolution options."""

    HIGH = "high"
    STANDARD = "standart"  # Match 'standart' spelling in ddgs library


class VideoDuration(str, Enum):
    """Video duration options."""

    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class ExtractFormat(str, Enum):
    """Extracted content output formats."""

    MARKDOWN = "text_markdown"
    PLAIN = "text_plain"
    RICH = "text_rich"
    HTML = "text"


class FetchFormat(str, Enum):
    """Fetch output formats matching crush's tool."""

    MARKDOWN = "markdown"
    TEXT = "text"
    HTML = "html"


class Config:
    """Global configuration object stored in typer context."""

    def __init__(
        self,
        proxy: Optional[str] = None,
        timeout: int = 10,
        verify: bool = True,
        max_retries: int = 3,
    ) -> None:
        self.proxy = proxy
        self.timeout = timeout
        self.verify = verify
        self.max_retries = max_retries


@app.callback()
def main_callback(
    ctx: typer.Context,
    proxy: Optional[str] = typer.Option(
        None,
        "--proxy",
        "-p",
        help="Proxy URL, comma-separated list, or file path to proxies.",
    ),
    timeout: int = typer.Option(
        10,
        "--timeout",
        "-t",
        help="Request timeout in seconds.",
    ),
    verify: bool = typer.Option(
        True,
        "--verify/--no-verify",
        help="Enable/disable SSL certification verification.",
    ),
    max_retries: int = typer.Option(
        3,
        "--max-retries",
        "-r",
        help="Maximum number of retries upon failures or timeouts.",
    ),
) -> None:
    """DuckDuckGo Search CLI wrapper using ddgs library."""
    ctx.obj = Config(
        proxy=proxy, timeout=timeout, verify=verify, max_retries=max_retries
    )


def _run_action(
    ctx: typer.Context,
    action_func: Callable[[Optional[str]], Any],
) -> Any:
    """Run an action with retry support, proxy rotation, and uniform error handling."""
    cfg: Config = ctx.obj
    proxies = parse_proxies(cfg.proxy)
    try:
        return execute_with_retry(action_func, proxies, max_retries=cfg.max_retries)
    except Exception as e:
        err_console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


def _execute_search(
    ctx: typer.Context,
    search_call: Callable[[DDGS], Any],
) -> Any:
    """Execute search query using client connection wrapper with type safety."""
    cfg: Config = ctx.obj

    def search_func(proxy: Optional[str]) -> Any:
        with DDGS(proxy=proxy, timeout=cfg.timeout, verify=cfg.verify) as ddgs:
            return search_call(ddgs)

    return _run_action(ctx, search_func)



def _handle_content_output(
    content: str,
    output: Optional[Path],
    is_markdown: bool,
    action_name: str,
) -> None:
    """Handle file saving or rendering markdown/plain text on stdout."""
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8")
        console.print(
            f"[bold green]Successfully saved {action_name} to {output}[/bold green]"
        )
    else:
        if is_markdown:
            from rich.markdown import Markdown

            console.print(Markdown(content))
        else:
            console.print(content)


@app.command()
def text(
    ctx: typer.Context,
    query: str = typer.Argument(..., help="Search query."),
    region: str = typer.Option("us-en", help="Region code (e.g. us-en, uk-en)."),
    safesearch: SafeSearch = typer.Option(
        SafeSearch.MODERATE, help="SafeSearch level."
    ),
    timelimit: Optional[str] = typer.Option(
        None, help="Time limit: d (day), w (week), m (month), y (year)."
    ),
    max_results: Optional[int] = typer.Option(
        10, help="Maximum number of results to return (None for all)."
    ),
    page: int = typer.Option(1, help="Page number to fetch."),
    backend: str = typer.Option("auto", help="Search backend to use."),
    format: OutputFormat = typer.Option(
        OutputFormat.TABLE, "--format", "-f", help="Output format."
    ),
) -> None:
    """Perform a text search across multiple search engines with auto-retries."""
    results = _execute_search(
        ctx,
        lambda ddgs: ddgs.text(
            query=query,
            region=region,
            safesearch=safesearch.value,
            timelimit=timelimit,
            max_results=max_results,
            page=page,
            backend=backend,
        ),
    )
    if not results:
        console.print("[yellow]No results found.[/yellow]")
        return
    display_results(results, "text", format.value)


@app.command()
def images(
    ctx: typer.Context,
    query: str = typer.Argument(..., help="Search query."),
    region: str = typer.Option("us-en", help="Region code (e.g. us-en, uk-en)."),
    safesearch: SafeSearch = typer.Option(
        SafeSearch.MODERATE, help="SafeSearch level."
    ),
    timelimit: Optional[str] = typer.Option(
        None, help="Time limit: d (day), w (week), m (month), y (year)."
    ),
    max_results: Optional[int] = typer.Option(10, help="Maximum number of results."),
    page: int = typer.Option(1, help="Page number to fetch."),
    backend: str = typer.Option("auto", help="Search backend to use."),
    size: Optional[ImageSize] = typer.Option(None, help="Filter by image size."),
    color: Optional[str] = typer.Option(
        None, help="Filter by color (e.g. color, Monochrome, red, etc.)."
    ),
    type_image: Optional[ImageType] = typer.Option(None, help="Filter by image type."),
    layout: Optional[ImageLayout] = typer.Option(None, help="Filter by layout."),
    license_image: Optional[str] = typer.Option(
        None, help="Filter by license (e.g. any, Public, Share, Modify)."
    ),
    format: OutputFormat = typer.Option(
        OutputFormat.TABLE, "--format", "-f", help="Output format."
    ),
) -> None:
    """Perform an image search with auto-retries and proxy rotation."""
    kwargs = {}
    if size:
        kwargs["size"] = size.value
    if color:
        kwargs["color"] = color
    if type_image:
        kwargs["type_image"] = type_image.value
    if layout:
        kwargs["layout"] = layout.value
    if license_image:
        kwargs["license_image"] = license_image

    results = _execute_search(
        ctx,
        lambda ddgs: ddgs.images(
            query=query,
            region=region,
            safesearch=safesearch.value,
            timelimit=timelimit,
            max_results=max_results,
            page=page,
            backend=backend,
            **kwargs,
        ),
    )
    if not results:
        console.print("[yellow]No results found.[/yellow]")
        return
    display_results(results, "images", format.value)


@app.command()
def videos(
    ctx: typer.Context,
    query: str = typer.Argument(..., help="Search query."),
    region: str = typer.Option("us-en", help="Region code (e.g. us-en, uk-en)."),
    safesearch: SafeSearch = typer.Option(
        SafeSearch.MODERATE, help="SafeSearch level."
    ),
    timelimit: Optional[str] = typer.Option(
        None, help="Time limit: d (day), w (week), m (month)."
    ),
    max_results: Optional[int] = typer.Option(10, help="Maximum number of results."),
    page: int = typer.Option(1, help="Page number to fetch."),
    backend: str = typer.Option("auto", help="Search backend to use."),
    resolution: Optional[VideoResolution] = typer.Option(
        None, help="Filter by resolution."
    ),
    duration: Optional[VideoDuration] = typer.Option(None, help="Filter by duration."),
    license_videos: Optional[str] = typer.Option(
        None, help="Filter by video license (e.g. creativeCommon, youtube)."
    ),
    format: OutputFormat = typer.Option(
        OutputFormat.TABLE, "--format", "-f", help="Output format."
    ),
) -> None:
    """Perform a video search with auto-retries and proxy rotation."""
    kwargs = {}
    if resolution:
        kwargs["resolution"] = resolution.value
    if duration:
        kwargs["duration"] = duration.value
    if license_videos:
        kwargs["license_videos"] = license_videos

    results = _execute_search(
        ctx,
        lambda ddgs: ddgs.videos(
            query=query,
            region=region,
            safesearch=safesearch.value,
            timelimit=timelimit,
            max_results=max_results,
            page=page,
            backend=backend,
            **kwargs,
        ),
    )
    if not results:
        console.print("[yellow]No results found.[/yellow]")
        return
    display_results(results, "videos", format.value)


@app.command()
def news(
    ctx: typer.Context,
    query: str = typer.Argument(..., help="Search query."),
    region: str = typer.Option("us-en", help="Region code (e.g. us-en, uk-en)."),
    safesearch: SafeSearch = typer.Option(
        SafeSearch.MODERATE, help="SafeSearch level."
    ),
    timelimit: Optional[str] = typer.Option(
        None, help="Time limit: d (day), w (week), m (month)."
    ),
    max_results: Optional[int] = typer.Option(10, help="Maximum number of results."),
    page: int = typer.Option(1, help="Page number to fetch."),
    backend: str = typer.Option("auto", help="Search backend to use."),
    format: OutputFormat = typer.Option(
        OutputFormat.TABLE, "--format", "-f", help="Output format."
    ),
) -> None:
    """Perform a news search with auto-retries and proxy rotation."""
    results = _execute_search(
        ctx,
        lambda ddgs: ddgs.news(
            query=query,
            region=region,
            safesearch=safesearch.value,
            timelimit=timelimit,
            max_results=max_results,
            page=page,
            backend=backend,
        ),
    )
    if not results:
        console.print("[yellow]No results found.[/yellow]")
        return
    display_results(results, "news", format.value)


@app.command()
def books(
    ctx: typer.Context,
    query: str = typer.Argument(..., help="Search query."),
    max_results: Optional[int] = typer.Option(10, help="Maximum number of results."),
    page: int = typer.Option(1, help="Page number to fetch."),
    backend: str = typer.Option("auto", help="Search backend to use."),
    format: OutputFormat = typer.Option(
        OutputFormat.TABLE, "--format", "-f", help="Output format."
    ),
) -> None:
    """Perform a book search with auto-retries and proxy rotation."""
    results = _execute_search(
        ctx,
        lambda ddgs: ddgs.books(
            query=query,
            max_results=max_results,
            page=page,
            backend=backend,
        ),
    )
    if not results:
        console.print("[yellow]No results found.[/yellow]")
        return
    display_results(results, "books", format.value)


@app.command()
def extract(
    ctx: typer.Context,
    url: str = typer.Argument(..., help="The URL to fetch and extract."),
    fmt: ExtractFormat = typer.Option(
        ExtractFormat.MARKDOWN,
        "--format",
        "-f",
        help="Format to extract content as.",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Save extracted content to this file path instead of stdout.",
    ),
) -> None:
    """Fetch a URL and extract its main content with auto-retries and proxy rotation."""

    result = _execute_search(
        ctx,
        lambda ddgs: ddgs.extract(url=url, fmt=fmt.value)
    )
    content = result.get("content", "")

    # If bytes, decode or handle appropriately
    if isinstance(content, bytes):
        try:
            content_str = content.decode("utf-8")
        except UnicodeDecodeError:
            content_str = str(content)
    else:
        content_str = content

    # Apply robust markdown cleaning/anti-bloat formatting
    content_str = clean_markdown(content_str)
    _handle_content_output(
        content_str,
        output,
        is_markdown=(fmt == ExtractFormat.MARKDOWN),
        action_name="content",
    )


@app.command()
def fetch(
    ctx: typer.Context,
    url: str = typer.Argument(..., help="The URL to fetch directly."),
    fmt: FetchFormat = typer.Option(
        FetchFormat.MARKDOWN,
        "--format",
        "-f",
        help="Format to convert the HTML content to.",
    ),
    max_size: int = typer.Option(
        100 * 1024,
        "--max-size",
        "-s",
        help="Maximum content size in bytes before truncation.",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Save fetched content to this file path instead of stdout.",
    ),
) -> None:
    """Directly fetch a URL using httpx and convert its HTML content to markdown, text, or keep html."""

    def fetch_func(proxy: Optional[str]) -> str:
        return fetch_url(
            url=url,
            fmt=fmt.value,
            timeout=float(ctx.obj.timeout),
            verify=ctx.obj.verify,
            proxy=proxy,
            max_size=max_size,
        )

    content_str = _run_action(ctx, fetch_func)

    # Apply robust cleaning if format is markdown
    if fmt == FetchFormat.MARKDOWN:
        content_str = clean_markdown(content_str)

    _handle_content_output(
        content_str,
        output,
        is_markdown=(fmt == FetchFormat.MARKDOWN),
        action_name="fetched content",
    )


if __name__ == "__main__":
    app()
