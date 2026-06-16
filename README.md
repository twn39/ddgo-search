# ddgo-search

[![Tests](https://github.com/twn39/ddgo-search/actions/workflows/tests.yml/badge.svg)](https://github.com/twn39/ddgo-search/actions/workflows/tests.yml)
[![PyPI version](https://img.shields.io/pypi/v/ddgo-search.svg)](https://pypi.org/project/ddgo-search/)
[![Python versions](https://img.shields.io/pypi/pyversions/ddgo-search.svg)](https://pypi.org/project/ddgo-search/)

A highly resilient, token-efficient, and feature-rich Command Line Interface (CLI) wrapper around the DuckDuckGo Search (`ddgs`) Python library. It features built-in proxy rotation, rate-limiting, custom token-saving ASCII rendering, webpage extraction, and direct content fetching.

---

## ✨ Features

- **🌐 Comprehensive Query Support**: Subcommands for `text`, `images`, `videos`, `news`, `books`, and web page extraction/fetching.
- **🔄 Resilient Proxy Rotation**: Accepts single proxy URLs, comma-separated lists, or files containing lists of proxies. Automatically rotates proxy servers sequentially on failure.
- **⏱️ Process-Safe Rate Limiting**: Randomised delays (between 1.5s to 3.0s) are tracked globally using a system-level temporary file to ensure safe execution even when multiple commands are run concurrently.
- **⚡ Direct Web Fetching (`fetch`)**: Inspired by Charmbracelet's `crush` tool. Directly fetches and converts webpages using `httpx`, `BeautifulSoup`, and `markdownify` into beautiful plain text, markdown, or HTML, with auto-truncation limits (e.g., 100KB) to preserve context windows.
- **📊 Token-Efficient ASCII Layouts**: Formats console lists using space-padded ASCII dividers rather than heavy Unicode grids to save context window tokens when using LLM agents.

---

## 🚀 Installation

It is recommended to install and manage `ddgo-search` using [uv](https://github.com/astral-sh/uv).

### 1. Global Installation (As a CLI Tool)

To install it globally so that the `ddgo-search` command is available from anywhere:

```bash
# Install directly from PyPI
uv tool install ddgo-search

# Or install from GitHub
uv tool install git+https://github.com/twn39/ddgo-search.git
```

### 2. Local Development Installation

If you want to clone the repository and run it locally:

```bash
# Clone the repository
git clone https://github.com/twn39/ddgo-search.git
cd ddgo-search

# Install dependencies and sync virtual environment
uv sync
```

---

## 📖 CLI Usage

Invoke `ddgo-search` directly using `uv`:

```bash
uv run ddgo-search [GLOBAL-OPTIONS] COMMAND [ARGS]...
```

### Global Options

These options must be passed *before* any subcommand:

- `-p, --proxy TEXT`: Proxy URL, comma-separated list of proxy URLs, or file path containing proxies (one per line). Falls back to the `DDGS_PROXY` environment variable.
- `-t, --timeout INTEGER`: Request timeout in seconds (default: `10`).
- `--verify / --no-verify`: Enable/disable SSL certification verification (default: `--verify`).
- `-r, --max-retries INTEGER`: Maximum retries upon server failures or timeouts (default: `3`).

---

### Commands

#### 1. Text Search (`text`)
Search the web for text results with custom formatting.
```bash
uv run ddgo-search text "artificial intelligence" --format plain
uv run ddgo-search text "python programming" --format table --max-results 5
```

#### 2. Image Search (`images`)
Query and filter DuckDuckGo images.
```bash
uv run ddgo-search images "cute kittens" --size Large --color Monochrome
uv run ddgo-search images "space nebula" --layout Wide --format json
```

#### 3. Video Search (`videos`)
Search for videos with specific duration, resolution, or license filters.
```bash
uv run ddgo-search videos "golang tutorial" --resolution high --duration short
```
*Note: The CLI standard resolution parameter accepts standard English spelling `"standard"`. The underlying adapter layer automatically maps this to the third-party library's expected `"standart"` spelling.*

#### 4. News Search (`news`)
Query recent news.
```bash
uv run ddgo-search news "climate change" --timelimit w --format csv
```

#### 5. Book Search (`books`)
Search DuckDuckGo books.
```bash
uv run ddgo-search books "machine learning" --max-results 10
```

#### 6. Web Page Extract (`extract`)
Fetch and extract webpage content using DuckDuckGo's internal extraction backend.
```bash
uv run ddgo-search extract "https://example.com" --format markdown
```

#### 7. Direct Web Page Fetch (`fetch`)
Directly fetch a URL via `httpx` and convert its HTML content locally to Markdown, clean text (excluding scripts, styles, headers, footers), or HTML. Includes auto-truncation.
```bash
# Direct fetch and convert to Markdown
uv run ddgo-search fetch "https://example.com" --format markdown

# Direct fetch and extract readable plain text
uv run ddgo-search fetch "https://example.com" --format text

# Direct fetch and write to file
uv run ddgo-search fetch "https://example.com" --format markdown --output doc.md

# Set custom truncation limit (e.g. 5KB)
uv run ddgo-search fetch "https://example.com" --max-size 5120
```

---

## 🤖 Codex Subagent & Skill Integration

You can integrate `ddgo-search` as a custom subagent and skill in Codex (or other supported agents like Antigravity, Crush, and Claude Code) to handle all web search and page fetching tasks.

### 1. Global Installation (Recommended)

To allow Codex to automatically call the `ddgo-search` subagent across all your projects:

1. **Install the CLI globally** so it is available from any workspace directory:
   ```bash
   # Install globally using uv
   uv tool install .
   ```
2. **Install the Skills and Subagent Configurations** using the CLI installer:
   ```bash
   # Install skills globally (for Codex, Antigravity, Crush, and Claude Code)
   ddgo-search skills install

   # Install the subagent configuration globally (for Codex)
   ddgo-search agents install --target codex
   ```

### 2. Project-level Installation

If you only want this subagent and skill available inside this project directory:

1. Ensure the project is trusted in your `~/.codex/config.toml`:
   ```toml
   [projects."/absolute/path/to/ddgo-search"]
   trust_level = "trusted"
   ```
2. Install the skills and agents locally:
   ```bash
   # Install skills locally
   ddgo-search skills install --local

   # Install the subagent configuration locally
   ddgo-search agents install --target codex --local
   ```
3. The packaged configurations are located at:
   - Skill: [SKILL.md](file:///Users/2342184/programs/ddgs-search/src/ddgo_search/resources/skills/ddgo-search-skill/SKILL.md)
   - Subagent Config: [ddgo-search.toml](file:///Users/2342184/programs/ddgs-search/src/ddgo_search/resources/agents/ddgo-search.toml)

### 3. Usage

Once the skill and subagent are installed globally, Codex can delegate searches automatically when prompted. You can trigger it explicitly by prompting:

> "使用网络查找关于..."

---

## 🧪 Development & Testing

Run the comprehensive unit test suite:

```bash
uv run pytest
```

Our tests mock the `DDGSAdapter` and the underlying `ddgs.DDGS` library to ensure that CLI routing, parameter translations, and network activities are validated robustly, instantly, and offline.
