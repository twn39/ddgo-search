"""Presentation and formatting helpers for ddgo-search CLI outputs."""

import csv
import io
import json
import sys
from typing import Any, Callable, Dict, List, Tuple

from rich.console import Console

console = Console()
err_console = Console(stderr=True)


def format_json(results: Any) -> str:
    """Format results as pretty printed JSON string."""
    from dataclasses import asdict, is_dataclass

    serialized = results
    if isinstance(results, list):
        serialized = [asdict(r) if is_dataclass(r) else r for r in results]
    elif is_dataclass(results):
        serialized = asdict(results)
    return json.dumps(serialized, indent=2, ensure_ascii=False)


def format_csv(results: List[Any]) -> str:
    """Format results as a CSV string."""
    if not results:
        return ""

    from dataclasses import asdict, is_dataclass

    dicts = [asdict(r) if is_dataclass(r) else r for r in results]
    output = io.StringIO()
    # Use keys from the first item as headers
    headers = list(dicts[0].keys())
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    for row in dicts:
        writer.writerow(row)
    return output.getvalue()


def truncate(val: Any, max_len: int) -> str:
    """Truncate string to max_len with ellipsis."""
    s = str(val or "").replace("\n", " ").strip()
    if len(s) > max_len:
        return s[: max_len - 3] + "..."
    return s


def format_simple_table(
    headers: List[str], rows: List[List[str]], width: int | None = None
) -> str:
    """Format list of rows as a token-efficient space-padded ASCII table using Rich Table for auto-wrapping and no truncation."""
    from rich.table import Table

    # Fallback to the global console's width if not specified
    table_width = width or console.width
    console_capture = Console(color_system=None, width=table_width)
    table = Table(
        box=None, show_header=True, header_style="", padding=(0, 3), pad_edge=False
    )
    for h in headers:
        table.add_column(h, overflow="fold")
    for row in rows:
        table.add_row(*[str(val) for val in row])
    with console_capture.capture() as capture:
        console_capture.print(table)
    lines = capture.get().splitlines()
    stripped_lines = [line.rstrip() for line in lines]
    while stripped_lines and not stripped_lines[0]:
        stripped_lines.pop(0)
    while stripped_lines and not stripped_lines[-1]:
        stripped_lines.pop(-1)

    # Insert divider below header (or handle empty lists safely)
    if stripped_lines:
        max_len = max(len(line) for line in stripped_lines)
        divider = "-" * max_len
        stripped_lines.insert(1, divider)

    return "\n".join(stripped_lines) + "\n"


def print_table_text(results: List[Any]) -> None:
    """Print text search results in a space-saving ASCII Table."""
    headers = ["Index", "Title", "URL", "Snippet"]
    rows = []
    for i, res in enumerate(results, 1):
        rows.append(
            [
                str(i),
                res.title or "",
                res.url or "",
                res.body or "",
            ]
        )
    console.print(format_simple_table(headers, rows))


def print_table_images(results: List[Any]) -> None:
    """Print image search results in a space-saving ASCII Table."""
    headers = ["Index", "Title", "Resolution", "Source", "Image URL"]
    rows = []
    for i, res in enumerate(results, 1):
        w = res.width
        h = res.height
        resolution = f"{w}x{h}" if w and h else "Unknown"
        rows.append(
            [
                str(i),
                res.title or "",
                resolution,
                res.source or "",
                res.url or "",
            ]
        )
    console.print(format_simple_table(headers, rows))


def print_table_news(results: List[Any]) -> None:
    """Print news search results in a space-saving ASCII Table."""
    headers = ["Date", "Title", "Source", "URL", "Snippet"]
    rows = []
    for res in results:
        rows.append(
            [
                res.date or "",
                res.title or "",
                res.source or "",
                res.url or "",
                res.body or "",
            ]
        )
    console.print(format_simple_table(headers, rows))


def print_table_videos(results: List[Any]) -> None:
    """Print video search results in a space-saving ASCII Table."""
    headers = ["Index", "Title", "Duration", "Publisher", "Published", "URL"]
    rows = []
    for i, res in enumerate(results, 1):
        rows.append(
            [
                str(i),
                res.title or "",
                res.duration or "",
                res.publisher or "",
                res.published or "",
                res.url or "",
            ]
        )
    console.print(format_simple_table(headers, rows))


def print_table_books(results: List[Any]) -> None:
    """Print book search results in a space-saving ASCII Table."""
    headers = ["Index", "Title", "Author", "Publisher", "Info", "URL"]
    rows = []
    for i, res in enumerate(results, 1):
        rows.append(
            [
                str(i),
                res.title or "",
                res.author or "",
                res.publisher or "",
                res.info or "",
                res.url or "",
            ]
        )
    console.print(format_simple_table(headers, rows))


def print_plain_text(results: List[Any]) -> None:
    """Print text search results as plain text."""
    for i, res in enumerate(results, 1):
        console.print(f"[bold cyan]{i}. {res.title}[/bold cyan]")
        console.print(f"[blue]{res.url}[/blue]")
        console.print(f"{res.body}\n")


def print_plain_images(results: List[Any]) -> None:
    """Print image search results as plain text."""
    for i, res in enumerate(results, 1):
        w = res.width
        h = res.height
        resolution = f" ({w}x{h})" if w and h else ""
        console.print(f"[bold cyan]{i}. {res.title}{resolution}[/bold cyan]")
        console.print(f"Source: {res.source}")
        console.print(f"Image: {res.url}\n")


def print_plain_news(results: List[Any]) -> None:
    """Print news search results as plain text."""
    for i, res in enumerate(results, 1):
        date_str = f" [{res.date}]" if res.date else ""
        console.print(f"[bold cyan]{i}. {res.title}{date_str}[/bold cyan]")
        console.print(f"Source: [yellow]{res.source}[/yellow]")
        console.print(f"URL: [blue]{res.url}[/blue]")
        console.print(f"{res.body}\n")


def print_plain_videos(results: List[Any]) -> None:
    """Print video search results as plain text."""
    for i, res in enumerate(results, 1):
        dur = f" ({res.duration})" if res.duration else ""
        console.print(f"[bold cyan]{i}. {res.title}{dur}[/bold cyan]")
        console.print(f"Publisher: {res.publisher} | Published: {res.published}")
        console.print(f"URL: [blue]{res.url}[/blue]\n")


def print_plain_books(results: List[Any]) -> None:
    """Print book search results as plain text."""
    for i, res in enumerate(results, 1):
        console.print(f"[bold cyan]{i}. {res.title}[/bold cyan]")
        console.print(
            f"Author: [magenta]{res.author}[/magenta] | Publisher: {res.publisher}"
        )
        console.print(f"Info: {res.info}")
        console.print(f"URL: [blue]{res.url}[/blue]\n")


def print_json(results: List[Any]) -> None:
    """Print results as JSON."""
    console.print(format_json(results))


def print_csv(results: List[Any]) -> None:
    """Print results as CSV."""
    sys.stdout.write(format_csv(results))


FORMATTER_REGISTRY: Dict[Tuple[str, str], Callable[[List[Any]], None]] = {
    ("text", "plain"): print_plain_text,
    ("images", "plain"): print_plain_images,
    ("news", "plain"): print_plain_news,
    ("videos", "plain"): print_plain_videos,
    ("books", "plain"): print_plain_books,
    ("text", "table"): print_table_text,
    ("images", "table"): print_table_images,
    ("news", "table"): print_table_news,
    ("videos", "table"): print_table_videos,
    ("books", "table"): print_table_books,
}


def display_results(results: List[Any], category: str, fmt: str) -> None:
    """Display the results in the requested format using strategy lookup."""
    if fmt == "json":
        print_json(results)
        return
    if fmt == "csv":
        print_csv(results)
        return

    formatter = FORMATTER_REGISTRY.get((category, fmt))
    if not formatter:
        raise ValueError(
            f"No formatter registered for category '{category}' and format '{fmt}'"
        )

    formatter(results)
