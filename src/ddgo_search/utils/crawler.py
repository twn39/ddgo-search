"""Fallback search scraper using JS-free Lite DuckDuckGo."""

import random
from typing import List, Optional

from .rate_limit import ensure_rate_limit


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
                if not href or not isinstance(href, str):
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
                    inputs = {}
                    for inp in form.find_all("input"):
                        name = inp.get("name")
                        val = inp.get("value") or ""
                        if isinstance(name, str):
                            if isinstance(val, list):
                                val = " ".join(val)
                            inputs[name] = str(val)
                    action = form.get("action")
                    if not isinstance(action, str):
                        action = "/lite/"
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
