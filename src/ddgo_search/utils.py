"""Utility functions for ddgo-search CLI, including rate-limiting, proxy rotation, and resiliency."""

import json
import os
import random
import tempfile
import time
from typing import Any, Callable, List, Optional

from ddgs.exceptions import DDGSException, TimeoutException
from rich.console import Console

err_console = Console(stderr=True)


def ensure_rate_limit() -> None:
    """Enforce rate limits across processes using a shared temp file."""
    temp_dir = tempfile.gettempdir()
    rate_file = os.path.join(temp_dir, "ddgo_search_rate.json")

    # Generate a random gap between 1.5 and 3.0 seconds
    required_gap = random.uniform(1.5, 3.0)

    try:
        if os.path.exists(rate_file):
            with open(rate_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                last_time = data.get("last_time", 0.0)

            elapsed = time.time() - last_time
            if elapsed < required_gap:
                sleep_time = required_gap - elapsed
                time.sleep(sleep_time)
    except Exception:
        # Ignore rate limiting failures to avoid blocking users
        pass

    # Update last request time
    try:
        with open(rate_file, "w", encoding="utf-8") as f:
            json.dump({"last_time": time.time()}, f)
    except Exception:
        pass


def parse_proxies(proxy_arg: Optional[str]) -> List[Optional[str]]:
    """Parse comma-separated proxy string or a file containing proxies."""
    if not proxy_arg:
        env_proxy = os.environ.get("DDGS_PROXY")
        if env_proxy:
            proxy_arg = env_proxy
        else:
            return [None]

    # Check if proxy_arg points to an existing file
    if os.path.exists(proxy_arg):
        try:
            with open(proxy_arg, "r", encoding="utf-8") as f:
                lines: List[Optional[str]] = [
                    line.strip() for line in f if line.strip()
                ]
                return lines if lines else [None]
        except Exception:
            pass

    proxies: List[Optional[str]] = [
        p.strip() for p in proxy_arg.split(",") if p.strip()
    ]
    return proxies if proxies else [None]


def execute_with_retry(
    func: Callable[[Optional[str]], Any],
    proxies: List[Optional[str]],
    max_retries: int = 3,
) -> Any:
    """Execute standard DDGS query with exponential backoff and proxy rotation."""
    attempt = 0
    proxy_index = 0

    while attempt < max_retries:
        ensure_rate_limit()
        current_proxy = proxies[proxy_index % len(proxies)]

        try:
            return func(current_proxy)
        except (DDGSException, TimeoutException, Exception) as e:
            attempt += 1
            if attempt >= max_retries:
                raise e

            # Exponential backoff with jitter: 2^attempt + uniform(-0.5, 0.5)
            backoff = (2**attempt) + random.uniform(-0.5, 0.5)
            backoff = max(0.5, backoff)

            if len(proxies) > 1:
                proxy_index += 1
                next_proxy = proxies[proxy_index % len(proxies)]
                err_console.print(
                    f"[yellow]Attempt {attempt} failed: {e}. "
                    f"Retrying in {backoff:.2f}s with proxy: {next_proxy}...[/yellow]",
                )
            else:
                err_console.print(
                    f"[yellow]Attempt {attempt} failed: {e}. "
                    f"Retrying in {backoff:.2f}s...[/yellow]",
                )
            time.sleep(backoff)


def clean_markdown(content: str) -> str:
    """Clean markdown text by removing duplicate blank lines & trailing space."""
    if not content:
        return ""

    # Collapse three or more consecutive newlines into exactly two
    lines = content.split("\n")
    cleaned_lines = []
    blank_count = 0

    for line in lines:
        stripped = line.rstrip()
        if not stripped:
            blank_count += 1
            if blank_count <= 1:
                cleaned_lines.append("")
        else:
            blank_count = 0
            cleaned_lines.append(stripped)

    return "\n".join(cleaned_lines).strip()


def fetch_url(
    url: str,
    fmt: str = "markdown",
    timeout: float = 30.0,
    verify: bool = True,
    proxy: Optional[str] = None,
    max_size: int = 100 * 1024,  # 100KB
) -> str:
    """Fetch URL directly with httpx and convert/clean based on target format."""
    import httpx
    from bs4 import BeautifulSoup
    import markdownify

    # Custom headers imitating modern browser headers
    headers = {
        "User-Agent": "ddgo-search/0.1.0 (Direct Fetch; similar to crush/1.0)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "max-age=0",
    }

    with httpx.Client(
        proxy=proxy, timeout=timeout, verify=verify, follow_redirects=True
    ) as client:
        response = client.get(url, headers=headers)
        response.raise_for_status()

        # Check for valid UTF-8
        try:
            content = response.text
        except UnicodeDecodeError as e:
            raise ValueError("Response content is not valid UTF-8") from e

        content_type = response.headers.get("content-type", "").lower()
        is_html = (
            "text/html" in content_type
            or url.endswith(".html")
            or url.endswith(".htm")
            or "<html" in content[:200].lower()
        )

        if is_html:
            soup = BeautifulSoup(content, "html.parser")
            if fmt == "text":
                # Clean text extraction: remove scripts, styles, metadata, and navs
                for element in soup(["script", "style", "header", "footer", "nav"]):
                    element.decompose()
                text = soup.get_text(separator=" ")
                content = " ".join(text.split())
            elif fmt == "markdown":
                # Convert HTML to Markdown using markdownify
                content = markdownify.markdownify(content, heading_style="ATX").strip()
            elif fmt == "html":
                # Extract <body> of HTML document
                body = soup.find("body")
                if body:
                    body_html = str(body)
                    content = f"<html>\n<body>\n{body_html}\n</body>\n</html>"
                else:
                    content = f"<html>\n<body>\n{content}\n</body>\n</html>"

        # Apply truncation if length of encoded bytes exceeds max_size
        encoded_content = content.encode("utf-8")
        if len(encoded_content) > max_size:
            truncated_bytes = encoded_content[:max_size]
            content = truncated_bytes.decode("utf-8", errors="ignore")
            content += f"\n\n[Content truncated to {max_size} bytes]"

        return content
