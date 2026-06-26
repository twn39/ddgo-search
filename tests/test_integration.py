"""Integration tests for ddgo-search."""

import http.server
import json
import os
import tempfile
import threading
import time
import urllib.request
from pathlib import Path
from typing import Generator

import pytest
from typer.testing import CliRunner

# Mock getproxies to return empty dict (disables macOS system configuration proxy settings)
urllib.request.getproxies = lambda: dict[str, str]()  # type: ignore

from ddgo_search.cli import app  # noqa: E402
from ddgo_search.utils import ensure_rate_limit, parse_proxies  # noqa: E402


@pytest.fixture(autouse=True)
def clean_env_proxies(monkeypatch) -> Generator[None, None, None]:
    """Ensure proxy environment variables and system settings do not interfere with local integration tests."""
    import urllib.request

    monkeypatch.setattr(urllib.request, "getproxies", lambda: dict[str, str]())

    old_env = {}
    proxy_vars = [
        "http_proxy",
        "https_proxy",
        "all_proxy",
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
    ]
    for var in proxy_vars:
        if var in os.environ:
            old_env[var] = os.environ[var]
            del os.environ[var]
    yield
    for var, val in old_env.items():
        os.environ[var] = val


class MockHTMLHandler(http.server.BaseHTTPRequestHandler):
    """Simple HTTP request handler that returns mock HTML content."""

    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        html = """
        <html>
            <head><title>Integration Test Page</title></head>
            <body>
                <h1>Integration Server</h1>
                <p>Hello from the integration test HTTP server!</p>
            </body>
        </html>
        """
        self.wfile.write(html.encode("utf-8"))

    def log_message(self, format: str, *args: str) -> None:
        # Suppress logging to stderr during tests to keep console clean
        pass


@pytest.fixture(scope="module")
def local_http_server() -> Generator[str, None, None]:
    """Start a lightweight local HTTP server in a background thread."""
    server = http.server.HTTPServer(("127.0.0.1", 0), MockHTMLHandler)
    addr = server.server_address
    ip, port = addr[0], addr[1]
    url = f"http://{ip}:{port}/"

    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

    yield url

    server.shutdown()
    thread.join()


def test_fetch_local_server_integration(local_http_server: str) -> None:
    """Test that the fetch command can request a real local HTTP server and parse it."""
    runner = CliRunner()
    result = runner.invoke(app, ["fetch", local_http_server, "--format", "markdown"])

    assert result.exit_code == 0
    assert "Integration Server" in result.stdout
    assert "Hello from the integration test HTTP server!" in result.stdout


def test_fetch_output_file_integration(local_http_server: str, tmp_path: Path) -> None:
    """Test fetching from a real server and writing the converted output directly to a file."""
    runner = CliRunner()
    out_file = tmp_path / "integration_fetch.md"
    result = runner.invoke(
        app, ["fetch", local_http_server, "--format", "text", "--output", str(out_file)]
    )

    assert result.exit_code == 0
    assert "Successfully saved fetched content" in result.stdout
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "Integration Server" in content
    assert "Hello from the integration test HTTP server!" in content


def test_proxy_file_parsing_integration(tmp_path: Path) -> None:
    """Test that parse_proxies correctly reads proxy strings and local files."""
    # Write a mock proxy list file
    proxy_file = tmp_path / "proxies.txt"
    proxy_file.write_text(
        "http://proxy1.example.com:8080\nhttp://proxy2.example.com:8080\n",
        encoding="utf-8",
    )

    proxies = parse_proxies(str(proxy_file))
    assert proxies == [
        "http://proxy1.example.com:8080",
        "http://proxy2.example.com:8080",
    ]


def test_rate_limiting_integration() -> None:
    """Test that ensure_rate_limit correctly writes and updates the rate limit timestamp in the temp file."""
    # Enforce rate limit to verify it reads/updates the temp file correctly
    ensure_rate_limit()

    temp_dir = tempfile.gettempdir()
    rate_file = os.path.join(temp_dir, "ddgo_search_rate_local.json")

    assert os.path.exists(rate_file)

    with open(rate_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "last_time" in data
    assert isinstance(data["last_time"], float)
    assert abs(data["last_time"] - time.time()) < 5.0


def test_fetch_github_integration() -> None:
    """Test fetching from the real Github repository URL provided by the user."""
    runner = CliRunner()
    result = runner.invoke(
        app, ["fetch", "https://github.com/twn39/ddgo-search", "--format", "markdown"]
    )

    assert result.exit_code == 0
    # Github repository page should contain twn39/ddgo-search
    assert "ddgo-search" in result.stdout.lower()


def test_ensure_rate_limit_concurrency() -> None:
    """Test that ensure_rate_limit serializes calls on the same proxy and parallelizes on different proxies."""
    from unittest.mock import patch

    # We mock random.uniform to return a constant 0.3s gap to keep the test fast but measurable
    with patch("random.uniform", return_value=0.3):
        events = []

        def run_search(proxy: str | None):
            start = time.time()
            ensure_rate_limit(proxy)
            end = time.time()
            events.append((proxy, start, end))

        # 1. Test serialization on the SAME proxy (or local IP)
        t1 = threading.Thread(target=run_search, args=(None,))
        t2 = threading.Thread(target=run_search, args=(None,))

        # Start t1, wait a tiny bit to make sure it enters first, then start t2
        t1.start()
        time.sleep(0.05)
        t2.start()

        t1.join()
        t2.join()

        # Sort events by start time to handle thread scheduling differences
        events.sort(key=lambda x: x[1])
        p1, s1, e1 = events[0]
        p2, s2, e2 = events[1]

        assert p1 is None
        assert p2 is None
        # t2 must have waited at least 0.25s after t1 started (specifically required_gap minus elapsed)
        assert e2 - s1 >= 0.25

        # 2. Test parallelization on DIFFERENT proxies
        events.clear()

        # Wait to clear any lingering lock interval
        time.sleep(0.3)

        t3 = threading.Thread(target=run_search, args=("http://proxy1:8080",))
        t4 = threading.Thread(target=run_search, args=("http://proxy2:8080",))

        t3.start()
        t4.start()

        t3.join()
        t4.join()

        # Both should finish quickly without serializing with each other (duration < 0.2s)
        for _, s, e in events:
            assert e - s < 0.2


def test_scrape_ddg_lite() -> None:
    """Test scrape_ddg_lite crawler directly and verify multi-page pagination."""
    from ddgo_search.utils import scrape_ddg_lite

    results = scrape_ddg_lite("python programming", max_results=12)

    assert len(results) == 12
    for r in results:
        assert isinstance(r, dict)
        assert "title" in r
        assert "url" in r
        assert "body" in r
        assert r["url"].startswith("http")


def test_ddgs_adapter_fallback_to_lite() -> None:
    """Test that DDGSAdapter.text falls back to scrape_ddg_lite when the primary client fails."""
    from unittest.mock import patch
    from ddgo_search.adapter import DDGSAdapter
    from ddgs.exceptions import DDGSException

    with patch("ddgs.DDGS.text", side_effect=DDGSException("Mocked DDG SDK Failure")):
        with DDGSAdapter() as adapter:
            results = adapter.text("python programming", max_results=3)

            assert len(results) == 3
            for r in results:
                assert r.title
                assert r.url
                assert r.body
                assert r.url.startswith("http")
