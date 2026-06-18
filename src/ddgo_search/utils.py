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


def ensure_rate_limit(proxy: Optional[str] = None) -> None:
    """Enforce rate limits across processes using proxy-specific file-locking."""
    import hashlib

    temp_dir = tempfile.gettempdir()

    # Generate a unique key for the proxy to isolate rate limits per outbound IP
    if proxy:
        proxy_hash = hashlib.md5(proxy.encode("utf-8")).hexdigest()[:12]
        key = f"proxy_{proxy_hash}"
    else:
        key = "local"

    lock_file = os.path.join(temp_dir, f"ddgo_search_rate_{key}.lock")
    rate_file = os.path.join(temp_dir, f"ddgo_search_rate_{key}.json")

    # Generate a random gap between 1.0 and 2.5 seconds
    required_gap = random.uniform(1.0, 2.5)

    lock_fd = None
    try:
        lock_fd = open(lock_file, "w")

        # Try fcntl (Unix/macOS)
        try:
            import fcntl

            fcntl.flock(lock_fd, fcntl.LOCK_EX)
        except (ImportError, AttributeError):
            # Try msvcrt (Windows)
            try:
                import msvcrt

                msvcrt.locking(lock_fd.fileno(), msvcrt.LK_LOCK, 1)
            except (ImportError, AttributeError):
                pass  # Fallback to lock-free sleep

        # Read last request timestamp
        last_time = 0.0
        if os.path.exists(rate_file):
            try:
                with open(rate_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    last_time = data.get("last_time", 0.0)
            except Exception:
                pass

        elapsed = time.time() - last_time
        if elapsed < required_gap:
            sleep_time = required_gap - elapsed
            time.sleep(sleep_time)

        # Update last request time
        try:
            with open(rate_file, "w", encoding="utf-8") as f:
                json.dump({"last_time": time.time()}, f)
            # Make sure it writes to disk immediately
            lock_fd.flush()
            os.fsync(lock_fd.fileno())
        except Exception:
            pass

    except Exception:
        # Fallback lock-free rate limiter in case of permission errors or other failures
        try:
            if os.path.exists(rate_file):
                with open(rate_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    last_time = data.get("last_time", 0.0)
                elapsed = time.time() - last_time
                if elapsed < required_gap:
                    time.sleep(required_gap - elapsed)
            with open(rate_file, "w", encoding="utf-8") as f:
                json.dump({"last_time": time.time()}, f)
        except Exception:
            pass
    finally:
        if lock_fd:
            try:
                lock_fd.close()
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
        current_proxy = proxies[proxy_index % len(proxies)]
        ensure_rate_limit(current_proxy)

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


def scrape_ddg_lite(
    query: str,
    region: str = "us-en",
    safesearch: str = "moderate",
    timelimit: Optional[str] = None,
    max_results: Optional[int] = 10,
    proxy: Optional[str] = None,
    timeout: float = 10.0,
    verify: bool = True,
) -> List[dict]:
    """Perform a DuckDuckGo search using the JavaScript-free Lite version.

    This acts as a Dual-Engine fallback mechanism.
    """
    import httpx
    from bs4 import BeautifulSoup
    from urllib.parse import urlparse, parse_qs

    if max_results is None or max_results <= 0:
        max_results = 10

    # Map SafeSearch level to kp
    kp_map = {"on": "1", "moderate": "-1", "off": "-2"}
    kp = kp_map.get(safesearch.lower(), "-1")

    # Map region
    kl = region if region else "wt-wt"

    # Map timelimit (df)
    df = timelimit if timelimit else ""

    headers = {
        "User-Agent": random.choice(
            [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15",
            ]
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "identity",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
    }

    def clean_ddg_url(raw_url: str) -> str:
        if raw_url.startswith("//"):
            raw_url = "https:" + raw_url
        if "uddg=" in raw_url:
            try:
                parsed = urlparse(raw_url)
                qs = parse_qs(parsed.query)
                if "uddg" in qs:
                    return qs["uddg"][0]
            except Exception:
                pass
        return raw_url

    results: List[dict] = []

    # Initial GET URL
    params = {"q": query, "kl": kl}
    if df:
        params["df"] = df
    if kp:
        params["kp"] = kp

    current_url = "https://lite.duckduckgo.com/lite/"
    method = "GET"
    payload = None

    with httpx.Client(
        proxy=proxy, timeout=timeout, verify=verify, follow_redirects=True
    ) as client:
        while len(results) < max_results:
            ensure_rate_limit(proxy)

            if method == "GET":
                response = client.get(current_url, params=params, headers=headers)
            else:
                headers["Origin"] = "https://lite.duckduckgo.com"
                headers["Referer"] = "https://lite.duckduckgo.com/lite/"
                response = client.post(current_url, data=payload, headers=headers)

            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            # Parse search results
            links = soup.find_all("a", class_="result-link")
            if not links:
                break

            new_results_added = False
            for link in links:
                title = link.get_text(strip=True)
                href = link.get("href")
                if not href:
                    continue
                url_clean = clean_ddg_url(href)

                # Check next row for snippet
                body = ""
                parent_tr = link.find_parent("tr")
                if parent_tr:
                    next_tr = parent_tr.find_next_sibling("tr")
                    if next_tr:
                        snippet_td = next_tr.find("td", class_="result-snippet")
                        if snippet_td:
                            body = snippet_td.get_text(strip=True)

                results.append({"title": title, "url": url_clean, "body": body})
                new_results_added = True
                if len(results) >= max_results:
                    break

            if not new_results_added:
                break

            # Check pagination
            next_form = None
            for form in soup.find_all("form"):
                submit_btn = form.find("input", type="submit", value="Next Page >")
                if submit_btn:
                    inputs = {
                        inp.get("name"): inp.get("value")
                        for inp in form.find_all("input")
                        if inp.get("name")
                    }
                    action = form.get("action") or "/lite/"
                    next_form = (action, inputs)
                    break

            if not next_form or len(results) >= max_results:
                break

            action, payload = next_form
            current_url = (
                "https://lite.duckduckgo.com" + action
                if action.startswith("/")
                else action
            )
            method = "POST"
            params = {}  # Clear params for POST request

    return results[:max_results]
