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
├── src/
│   └── ddgo_search/
│       ├── __init__.py  # Package metadata (defines __version__)
│       ├── adapter.py   # Adapter shielding CLI from third-party SDK changes, mapping DTOs and exceptions
│       ├── cli.py       # Typer CLI application structure, parameters, commands
│       ├── exceptions.py# Custom domains/search application exception types
│       ├── installer.py # Decoupled administrative command handlers (skills/agents install)
│       └── utils.py     # Resiliency, rate limiting, and output formatting helpers
└── tests/
    ├── test_adapter.py  # Unit tests verifying adapter translations and exception mappings
    └── test_cli.py      # Pytest unit tests utilizing extensive mocking of DDGSAdapter
```

---

## 🏗️ Architecture & Data Flow

The project is a resilient CLI wrapper around the Python `ddgs` (DuckDuckGo Search) library.

### Control Flow
1. **Invocation**: The user invokes `ddgo-search`.
2. **Context Setup**: `main_callback()` is triggered, parsing global options (`--proxy`, `--timeout`, `--verify`, `--max-retries`). It builds a `Config` object and attaches it to the Typer context (`ctx.obj`).
3. **Command Routing**: Typer routes execution to a specific subcommand handler (`text`, `images`, `videos`, `news`, `books`, `extract`, `fetch`).
4. **Execution & Resiliency**: The subcommand delegates execution to the `DDGSAdapter` inside `_execute_search()`. The adapter translates input options and executes the query through `execute_with_retry()`.
5. **Rate Limiting**: Within `execute_with_retry()`, `ensure_rate_limit()` is called. It checks the global `ddgo_search_rate.json` file to ensure a randomized gap of **1.5 to 3.0 seconds** has elapsed since the last request across any process.
6. **Query & Proxy Rotation**: The wrapper tries to execute the query. If a proxy was provided (single, comma-separated, or file path), the query uses it. On failure, it performs exponential backoff with jitter and rotates to the next proxy.
7. **Formatting**: If successful, normalized DTO results are returned to the CLI and passed to `display_results()` which maps formatting functions (`json`, `csv`, `plain`, `table`) according to the active query category.

---

## 🎨 Design & Style Patterns

- **CLI Framework**: [Typer](https://typer.tiangolo.com/) is used for defining commands, arguments, option groups, and help text. Subcommands match `ddgs` methods directly.
- **Terminal output**: [Rich](https://github.com/Textualize/rich) is used for rendering plain and markdown outputs.
- **Output Formats**:
  - `plain`: Default clean colored output optimized for terminal readability and token efficiency.
  - `table`: Space-saving ASCII table. Uses Rich Table with edge padding disabled to auto-wrap long content cleanly without any truncation.
  - `json`: Standard JSON-serialized dump.
  - `csv`: Standard CSV format.

- **Default Format and Non-Truncation**:
  - The CLI subcommands default to `--format plain` to preserve tokens and offer clean, readable output by default.
  - When choosing `--format table`, the table is rendered using Rich with line-wrapping and no string truncation, ensuring all content is completely preserved.

- **Scope Limiting & Search Operators**:
  - Built-in options such as `--region`, `--timelimit`, and `--safesearch` are exposed on CLI subcommands.
  - Advanced search operators (e.g. `site:github.com`, `filetype:pdf`, `intitle:`) can be used directly inside the query string.

---

## 🧪 Testing Approach

- **Resiliency Mocking**: Since live queries to DuckDuckGo are prone to rate-limiting and external network failures, **all CLI tests must mock the `DDGSAdapter` class**, while `tests/test_adapter.py` mocks the underlying `ddgs.DDGS` client to verify translation layers.
- **Instant Test Runs**: The `tests/test_cli.py` module defines an autouse fixture `mock_rate_limit` which patches `ddgo_search.utils.ensure_rate_limit` to instantly bypass rate limits, speeding up test suite execution.
- **CliRunner**: Use Typer's `CliRunner` for invoking and verifying standard outputs and exit codes.

---

## ⚠️ Non-Obvious Gotchas & Quirks

1. **Resolution & Extract Format Translation (Typos in `ddgs` library)**:
   - The third-party `ddgs` library expects `"standart"` as the value for standard resolution instead of `"standard"`, and verbose format values like `"text_markdown"`.
   - The CLI exposes standard clean options (`standard` and `markdown`). The mapping is performed dynamically inside `src/ddgo_search/adapter.py` to shield CLI callers from library anomalies. Do not revert to raw typo values in `cli.py` or enums.
2. **Rate Limiting Persistence**:
   - Rate limiting relies on a file named `ddgo_search_rate.json` written to the system's temporary directory (`tempfile.gettempdir()`). If writing/reading to/from this file fails, the application fails silently to avoid blocking execution.
3. **Proxy Input Formats**:
   - The `--proxy` option accepts a single proxy URL, a comma-separated list of proxy URLs, or a **file path** containing proxy URLs (one per line). The parser `parse_proxies()` detects local files dynamically.
4. **Markdown Cleaning**:
   - Web extraction results can contain bloated markup. The `clean_markdown` utility collapses three or more consecutive blank lines into exactly two and strips trailing whitespace from all lines.
5. **Direct Fetch (`fetch`) vs DDG Extract (`extract`)**:
   - The `extract` command uses DuckDuckGo's internal extraction backend via `ddgs.extract`.
   - The `fetch` command mimics Charmbracelet Crush's direct fetch tool by directly requesting the target URL via `httpx` and parsing it locally with `BeautifulSoup` and `markdownify` into `text`, `markdown`, or `html`. It also respects a `--max-size` limit (default 100KB) and truncates any content exceeding it.

## codegraph-gen

This project maintains a codebase knowledge graph at `.codegraph/`.

### Guidelines for AI Agents (Antigravity, Claude Code, Cursor, Roo Code, etc.)

You MUST follow these rules when working in this codebase:

1. **Prioritize the Knowledge Graph**:
   - Before answering architecture, design, or codebase structure questions, you **MUST** read [.codegraph/README.md](.codegraph/README.md) to understand the system overview, god nodes, and logical community structure.
   - Use [.codegraph/components/](.codegraph/components/) and [.codegraph/nodes/](.codegraph/nodes/) to navigate component boundaries, file relationships, and symbol definitions. This is much faster and more token-efficient than reading raw source files directly.

2. **AI Architectural Insights**:
   - Check [.codegraph/README.md](.codegraph/README.md) for a section titled `AI Architectural Insights`.
   - If this section is missing, incomplete, or contains placeholders, read [.codegraph/AGENT_PROMPT.md](.codegraph/AGENT_PROMPT.md), perform a deep architectural analysis of the project, and write your report into that section. Do not overwrite other sections.

3. **Keep Graph Sync'd**:
   - Whenever you create, delete, or modify code files, you **SHOULD** remind the user to run `codegraph build .` to rebuild the knowledge graph and keep it current.
   - When running the build command, exclude irrelevant or generated directories (e.g., third-party dependencies, build folders, or documentation) using the `-e`/`--exclude` flag to keep the graph focused and clean (e.g., `codegraph build . -e third_party/`).
