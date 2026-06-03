# Agent Guide - ddgo-search

This guide provides the essential technical context, architecture, commands, patterns, and non-obvious details/gotchas required for an AI agent to work efficiently in this repository.

---

## 🛠️ Essential Commands

The project uses [uv](https://github.com/astral-sh/uv) as its package and environment manager.

- **Run unit tests**:
  ```bash
  uv run pytest
  ```
- **Execute CLI directly in development**:
  ```bash
  uv run ddgo-search [COMMAND] [ARGS]...
  ```
  Example:
  ```bash
  uv run ddgo-search text "artificial intelligence" --format plain
  ```

---

## 📂 Code Organization & Structure

The repository has a clean, standard Python layout:

```text
├── .python-version      # Target Python version (>=3.12)
├── pyproject.toml       # Build metadata, CLI entry points, and dependencies
├── uv.lock              # Lockfile for the uv environment manager
├── src/
│   └── ddgo_search/
│       ├── __init__.py  # Package metadata (defines __version__)
│       ├── cli.py       # Typer CLI application structure, parameters, commands
│       └── utils.py     # Resiliency, rate limiting, and output formatting helpers
└── tests/
    └── test_cli.py      # Pytest unit tests utilizing extensive mocking
```

---

## 🏗️ Architecture & Data Flow

The project is a resilient CLI wrapper around the Python `ddgs` (DuckDuckGo Search) library.

### Control Flow
1. **Invocation**: The user invokes `ddgo-search`.
2. **Context Setup**: `main_callback()` is triggered, parsing global options (`--proxy`, `--timeout`, `--verify`, `--max-retries`). It builds a `Config` object and attaches it to the Typer context (`ctx.obj`).
3. **Command Routing**: Typer routes execution to a specific subcommand handler (`text`, `images`, `videos`, `news`, `books`, `extract`, `fetch`).
4. **Execution & Resiliency**: The subcommand invokes `execute_with_retry()`, supplying a search function matching the category.
5. **Rate Limiting**: Within `execute_with_retry()`, `ensure_rate_limit()` is called. It checks the global `ddgo_search_rate.json` file to ensure a randomized gap of **1.5 to 3.0 seconds** has elapsed since the last request across any process.
6. **Query & Proxy Rotation**: The wrapper tries to execute the query. If a proxy was provided (single, comma-separated, or file path), the query uses it. On failure, it performs exponential backoff with jitter and rotates to the next proxy.
7. **Formatting**: If successful, results are passed to `display_results()` which maps formatting functions (`json`, `csv`, `plain`, `table`) according to the active query category.

---

## 🎨 Design & Style Patterns

- **CLI Framework**: [Typer](https://typer.tiangolo.com/) is used for defining commands, arguments, option groups, and help text. Subcommands match `ddgs` methods directly.
- **Terminal output**: [Rich](https://github.com/Textualize/rich) is used for rendering plain and markdown outputs.
- **Output Formats**:
  - `table`: Custom space-efficient ASCII table. To minimize token waste, a custom ASCII generator `format_simple_table()` is used instead of heavy tables.
  - `json`: Standard JSON-serialized dump.
  - `csv`: Standard CSV format.
  - `plain`: Clean colored output optimized for terminal readability.

---

## 🧪 Testing Approach

- **Resiliency Mocking**: Since live queries to DuckDuckGo are prone to rate-limiting and external network failures, **all CLI tests must mock the `ddgs.DDGS` class**.
- **Instant Test Runs**: The `tests/test_cli.py` module defines an autouse fixture `mock_rate_limit` which patches `ddgo_search.utils.ensure_rate_limit` to instantly bypass rate limits, speeding up test suite execution.
- **CliRunner**: Use Typer's `CliRunner` for invoking and verifying standard outputs and exit codes.

---

## ⚠️ Non-Obvious Gotchas & Quirks

1. **Typo in the `ddgs` library (Video Resolution)**:
   - The third-party `ddgs` library expects `"standart"` as the value for standard resolution instead of `"standard"`.
   - **Do not "fix" this spelling** in `cli.py` or `VideoResolution` enum. It is defined as `STANDARD = "standart"` to correctly interface with the underlying library.
2. **Rate Limiting Persistence**:
   - Rate limiting relies on a file named `ddgo_search_rate.json` written to the system's temporary directory (`tempfile.gettempdir()`). If writing/reading to/from this file fails, the application fails silently to avoid blocking execution.
3. **Proxy Input Formats**:
   - The `--proxy` option accepts a single proxy URL, a comma-separated list of proxy URLs, or a **file path** containing proxy URLs (one per line). The parser `parse_proxies()` detects local files dynamically.
4. **Markdown Cleaning**:
   - Web extraction results can contain bloated markup. The `clean_markdown` utility collapses three or more consecutive blank lines into exactly two and strips trailing whitespace from all lines.
5. **Direct Fetch (`fetch`) vs DDG Extract (`extract`)**:
   - The `extract` command uses DuckDuckGo's internal extraction backend via `ddgs.extract`.
   - The `fetch` command mimics Charmbracelet Crush's direct fetch tool by directly requesting the target URL via `httpx` and parsing it locally with `BeautifulSoup` and `markdownify` into `text`, `markdown`, or `html`. It also respects a `--max-size` limit (default 100KB) and truncates any content exceeding it.

