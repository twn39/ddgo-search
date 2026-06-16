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
urllib.request.getproxies = lambda: {}

from ddgo_search.cli import app  # noqa: E402
from ddgo_search.utils import ensure_rate_limit, parse_proxies  # noqa: E402


@pytest.fixture(autouse=True)
def clean_env_proxies(monkeypatch) -> Generator[None, None, None]:
    """Ensure proxy environment variables and system settings do not interfere with local integration tests."""
    import urllib.request

    monkeypatch.setattr(urllib.request, "getproxies", lambda: {})

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
    # Enforce rate limit twice to verify it reads/updates the temp file correctly
    ensure_rate_limit()

    temp_dir = tempfile.gettempdir()
    rate_file = os.path.join(temp_dir, "ddgo_search_rate.json")

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
