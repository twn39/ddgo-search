"""Presentation and formatting helpers for ddgo-search CLI outputs."""

import csv
import io
import json
import sys
from typing import Any, Dict, List

from rich.console import Console

console = Console()
err_console = Console(stderr=True)


def format_json(results: Any) -> str:
    """Format results as pretty printed JSON string."""
    return json.dumps(results, indent=2, ensure_ascii=False)


def format_csv(results: List[Dict[str, Any]]) -> str:
    """Format results as a CSV string."""
    if not results:
        return ""

    output = io.StringIO()
    # Use keys from the first item as headers
    headers = list(results[0].keys())
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    for row in results:
        writer.writerow(row)
    return output.getvalue()


def truncate(val: Any, max_len: int) -> str:
    """Truncate string to max_len with ellipsis."""
    s = str(val or "").replace("\n", " ").strip()
    if len(s) > max_len:
        return s[: max_len - 3] + "..."
    return s


def format_simple_table(headers: List[str], rows: List[List[str]]) -> str:
    """Format list of rows as a token-efficient space-padded ASCII table."""
    # Find max width for each column
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(str(val)))

    # Format headers
    header_parts = []
    for i, h in enumerate(headers):
        if i == len(headers) - 1:
            header_parts.append(h)
        else:
            header_parts.append(f"{h:<{col_widths[i] + 3}}")
    header_str = "".join(header_parts)

    # Format rows
    row_strs = []
    for row in rows:
        row_parts = []
        for i, val in enumerate(row):
            val_str = str(val)
            if i == len(headers) - 1:
                row_parts.append(val_str)
            else:
                row_parts.append(f"{val_str:<{col_widths[i] + 3}}")
        row_strs.append("".join(row_parts))

    # Divider line based on the maximum line length of either header or any formatted row
    max_len = len(header_str)
    for row_str in row_strs:
        max_len = max(max_len, len(row_str))
    divider = "-" * max_len

    return f"{header_str}\n{divider}\n" + "\n".join(row_strs) + "\n"


def print_table_text(results: List[Dict[str, Any]]) -> None:
    """Print text search results in a space-saving ASCII Table."""
    headers = ["Index", "Title", "URL", "Snippet"]
    rows = []
    for i, res in enumerate(results, 1):
        rows.append(
            [
                str(i),
                truncate(res.get("title", ""), 40),
                truncate(res.get("url", ""), 35),
                truncate(res.get("body", ""), 65),
            ]
        )
    console.print(format_simple_table(headers, rows))


def print_table_images(results: List[Dict[str, Any]]) -> None:
    """Print image search results in a space-saving ASCII Table."""
    headers = ["Index", "Title", "Resolution", "Source", "Image URL"]
    rows = []
    for i, res in enumerate(results, 1):
        w = res.get("width", "")
        h = res.get("height", "")
        resolution = f"{w}x{h}" if w and h else "Unknown"
        rows.append(
            [
                str(i),
                truncate(res.get("title", ""), 35),
                resolution,
                truncate(res.get("source", ""), 20),
                truncate(res.get("url", ""), 45),
            ]
        )
    console.print(format_simple_table(headers, rows))


def print_table_news(results: List[Dict[str, Any]]) -> None:
    """Print news search results in a space-saving ASCII Table."""
    headers = ["Date", "Title", "Source", "URL", "Snippet"]
    rows = []
    for res in results:
        rows.append(
            [
                truncate(res.get("date", ""), 15),
                truncate(res.get("title", ""), 35),
                truncate(res.get("source", ""), 15),
                truncate(res.get("url", ""), 35),
                truncate(res.get("body", ""), 60),
            ]
        )
    console.print(format_simple_table(headers, rows))


def print_table_videos(results: List[Dict[str, Any]]) -> None:
    """Print video search results in a space-saving ASCII Table."""
    headers = ["Index", "Title", "Duration", "Publisher", "Published", "URL"]
    rows = []
    for i, res in enumerate(results, 1):
        rows.append(
            [
                str(i),
                truncate(res.get("title", ""), 40),
                truncate(res.get("duration", ""), 10),
                truncate(res.get("publisher", ""), 15),
                truncate(res.get("published", ""), 15),
                truncate(res.get("url", ""), 40),
            ]
        )
    console.print(format_simple_table(headers, rows))


def print_table_books(results: List[Dict[str, Any]]) -> None:
    """Print book search results in a space-saving ASCII Table."""
    headers = ["Index", "Title", "Author", "Publisher", "Info", "URL"]
    rows = []
    for i, res in enumerate(results, 1):
        rows.append(
            [
                str(i),
                truncate(res.get("title", ""), 35),
                truncate(res.get("author", ""), 20),
                truncate(res.get("publisher", ""), 15),
                truncate(res.get("info", ""), 25),
                truncate(res.get("url", ""), 35),
            ]
        )
    console.print(format_simple_table(headers, rows))


def print_plain_text(results: List[Dict[str, Any]]) -> None:
    """Print text search results as plain text."""
    for i, res in enumerate(results, 1):
        console.print(f"[bold cyan]{i}. {res.get('title')}[/bold cyan]")
        console.print(f"[blue]{res.get('url')}[/blue]")
        console.print(f"{res.get('body')}\n")


def print_plain_images(results: List[Dict[str, Any]]) -> None:
    """Print image search results as plain text."""
    for i, res in enumerate(results, 1):
        w = res.get("width", "")
        h = res.get("height", "")
        resolution = f" ({w}x{h})" if w and h else ""
        console.print(f"[bold cyan]{i}. {res.get('title')}{resolution}[/bold cyan]")
        console.print(f"Source: {res.get('source')}")
        console.print(f"Image: {res.get('url')}\n")


def print_plain_news(results: List[Dict[str, Any]]) -> None:
    """Print news search results as plain text."""
    for i, res in enumerate(results, 1):
        date_str = f" [{res.get('date')}]" if res.get("date") else ""
        console.print(f"[bold cyan]{i}. {res.get('title')}{date_str}[/bold cyan]")
        console.print(f"Source: [yellow]{res.get('source')}[/yellow]")
        console.print(f"URL: [blue]{res.get('url')}[/blue]")
        console.print(f"{res.get('body')}\n")


def print_plain_videos(results: List[Dict[str, Any]]) -> None:
    """Print video search results as plain text."""
    for i, res in enumerate(results, 1):
        dur = f" ({res.get('duration')})" if res.get("duration") else ""
        console.print(f"[bold cyan]{i}. {res.get('title')}{dur}[/bold cyan]")
        console.print(
            f"Publisher: {res.get('publisher')} | Published: {res.get('published')}"
        )
        console.print(f"URL: [blue]{res.get('url')}[/blue]\n")


def print_plain_books(results: List[Dict[str, Any]]) -> None:
    """Print book search results as plain text."""
    for i, res in enumerate(results, 1):
        console.print(f"[bold cyan]{i}. {res.get('title')}[/bold cyan]")
        console.print(
            f"Author: [magenta]{res.get('author')}[/magenta] | Publisher: {res.get('publisher')}"
        )
        console.print(f"Info: {res.get('info')}")
        console.print(f"URL: [blue]{res.get('url')}[/blue]\n")


def display_results(results: List[Dict[str, Any]], category: str, fmt: str) -> None:
    """Display the results in the requested format."""
    if fmt == "json":
        console.print(format_json(results))
    elif fmt == "csv":
        sys.stdout.write(format_csv(results))
    elif fmt == "plain":
        if category == "text":
            print_plain_text(results)
        elif category == "images":
            print_plain_images(results)
        elif category == "news":
            print_plain_news(results)
        elif category == "videos":
            print_plain_videos(results)
        elif category == "books":
            print_plain_books(results)
    else:  # "table"
        if category == "text":
            print_table_text(results)
        elif category == "images":
            print_table_images(results)
        elif category == "news":
            print_table_news(results)
        elif category == "videos":
            print_table_videos(results)
        elif category == "books":
            print_table_books(results)
