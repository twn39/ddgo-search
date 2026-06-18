"""Exposed utilities interface for ddgo-search CLI, providing backward compatibility."""

from .console import err_console
from .crawler import scrape_ddg_lite
from .network import execute_with_retry, fetch_url, parse_proxies
from .rate_limit import ensure_rate_limit
from .text import clean_markdown

__all__ = [
    "err_console",
    "scrape_ddg_lite",
    "execute_with_retry",
    "fetch_url",
    "parse_proxies",
    "ensure_rate_limit",
    "clean_markdown",
]
