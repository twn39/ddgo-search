---
name: ddgo-search-skill
description: Performs web search queries and fetches webpages. Use when the user asks to search the web, search Google/DuckDuckGo, retrieve search results, fetch or scrape web content, or when you need to search (搜索, 网络搜索, 网页抓取, 查资料). Supports subcommands text, images, videos, news, books, extract, and fetch.
dependencies: python>=3.11
allowed-tools:
  - bash
  - Bash
  - execute_command
---

# DDGo Search Skill

`ddgo-search` is a resilient, token-efficient CLI wrapper around the DuckDuckGo Search (`ddgs`) Python library. It provides robust rate-limiting, proxy rotation, webpage extraction, and direct content fetching.

## 📦 Installation

Before using this skill, ensure `ddgo-search` is installed. It is recommended to install it globally using `uv`:

1. **Install `uv`** (if not already installed):
   - macOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
   - Windows: `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`

2. **Install `ddgo-search`**:
   ```bash
   uv tool install ddgo-search
   ```

3. **Install the Skills configurations**:
   ```bash
   # Install the skills (for Codex, Antigravity, Crush, and Claude Code)
   ddgo-search skills install
   ```

## 🚀 Quick Start

Run commands directly (if installed via `uv tool install`) or using `uv run` (if executing inside the project directory):

```bash
# Text search (default format is ASCII table)
ddgo-search text "artificial intelligence"
# Or: uv run ddgo-search text "artificial intelligence"

# Direct URL fetch and convert to Markdown
ddgo-search fetch "https://example.com" --format markdown
# Or: uv run ddgo-search fetch "https://example.com" --format markdown
```

---

## 🛠️ CLI Reference

### Global Options
Pass global options *before* the subcommand:
- `-p, --proxy TEXT`: A single proxy URL, comma-separated list, or path to a file with proxies (one per line).
- `-t, --timeout INTEGER`: Request timeout in seconds (default: `10`).
- `-r, --max-retries INTEGER`: Maximum retries upon server failures or timeouts (default: `3`).
- `--verify / --no-verify`: Enable/disable SSL certification verification (default: `--verify`).

Example:
```bash
ddgo-search -p "http://proxy.example.com:8080" -t 15 text "latest technology"
```

### Subcommands

#### 1. Text Search (`text`)
Search the web for text results.
```bash
ddgo-search text "python programming" [OPTIONS]
```
- `--max-results INTEGER`: Maximum results to return (default: `10`).
- `--timelimit [d|w|m|y]`: Limit results to day, week, month, or year.
- `--region TEXT`: Region/country code (default: `us-en`).
- `--safesearch [on|moderate|off]`: Content filtering (default: `moderate`).
- `-f, --format [table|plain|json|csv]`: Output format (default: `plain`).

#### 2. Image Search (`images`)
Search for images.
```bash
ddgo-search images "space nebula" [OPTIONS]
```
- `--size [Small|Medium|Large|Wallpaper]`
- `--color [color|Monochrome|red|green|etc.]`
- `--type-image [photo|clipart|gif|transparent|line]`
- `--layout [Square|Tall|Wide]`
- `--license-image [any|Public|Share|Modify]`
- `--region TEXT`: Region/country code (default: `us-en`).
- `--safesearch [on|moderate|off]`: Content filtering (default: `moderate`).
- `-f, --format [table|plain|json|csv]` (default: `plain`).

#### 3. Video Search (`videos`)
Search for videos.
```bash
ddgo-search videos "rust tutorial" [OPTIONS]
```
- `--resolution [high|standard]`
- `--duration [short|medium|long]`
- `--license-videos [creativeCommon|youtube]`
- `--region TEXT`: Region/country code (default: `us-en`).
- `--safesearch [on|moderate|off]`: Content filtering (default: `moderate`).
- `-f, --format [table|plain|json|csv]` (default: `plain`).

*Note: The underlying library standard resolution expects `"standart"`. The CLI enum maps `"standard"` to `"standart"` automatically.*

#### 4. News Search (`news`)
Query recent news.
```bash
ddgo-search news "climate change" [OPTIONS]
```
- `--timelimit [d|w|m]`
- `--region TEXT`: Region/country code (default: `us-en`).
- `--safesearch [on|moderate|off]`: Content filtering (default: `moderate`).
- `-f, --format [table|plain|json|csv]` (default: `plain`).

#### 5. Book Search (`books`)
Search DuckDuckGo books.
```bash
ddgo-search books "machine learning" [OPTIONS]
```
- `--max-results INTEGER`: (default: `10`).
- `-f, --format [table|plain|json|csv]` (default: `plain`).

#### 6. Web Page Extract (`extract`)
Extract main content using DuckDuckGo's internal extraction backend.
```bash
ddgo-search extract "https://example.com" [OPTIONS]
```
- `-f, --format [text_markdown|text_plain|text_rich|text]` (default: `text_markdown`).
- `-o, --output PATH`: Save extracted content to file instead of printing.

#### 7. Direct Web Page Fetch (`fetch`)
Directly fetch a URL using `httpx` and convert its HTML content to Markdown, clean text, or raw HTML. **This is highly recommended for scraping specific pages bypasses DDG's extract servers.**
```bash
ddgo-search fetch "https://example.com" [OPTIONS]
```
- `-f, --format [markdown|text|html]` (default: `markdown`).
- `-s, --max-size INTEGER`: Maximum content size in bytes before truncation to preserve tokens (default: `102400` / 100KB).
- `-o, --output PATH`: Save content to file instead of printing.

---

## 🔍 Scope Limiting & Search Operators

You can narrow down search results by region, time recency, safety settings, or using direct query operators:

### CLI Options
- `--region TEXT`: Limits results to a specific region/country code (e.g., `us-en`, `cn-zh`).
- `--timelimit [d|w|m|y]`: Retrieves only recent results from the past day, week, month, or year.
- `--safesearch [on|moderate|off]`: Controls content filtering.

### Search Operators (within QUERY)
- `site:example.com`: Only return results within a specific website.
- `-site:example.com`: Exclude a specific website from results.
- `filetype:pdf`: Filter by file format (e.g., pdf, doc, ppt).
- `intitle:keyword`: Require keyword in the page title.
- `"exact phrase"`: Match exact word combination.

Example:
```bash
ddgo-search text "python site:stackoverflow.com" --timelimit m
```

---

## 🤖 Mandatory Search Strategies

When acting as an AI web content analysis agent, adhere strictly to the following developer instructions, behavior rules, and formatting standards.

#### Rules
1. **Be concise and direct** in your responses.
2. **Focus only on the information requested** in the user's prompt.
3. If the content is provided in a file path, **use the grep and view tools** to efficiently search through it.
4. When relevant, **quote specific sections** from the content to support your answer.
5. If the requested information is not found, **clearly state that**.
6. Any file paths you use **MUST be absolute**.
7. **IMPORTANT**: If you need information from a linked page or search result, run the `ddgo-search fetch` command via the Bash tool to retrieve the content.
8. **IMPORTANT**: If you need to search for more information, run the `ddgo-search text` command via the Bash tool.
9. **Analyze the content yourself** after fetching a link to extract what's needed.
10. Don't hesitate to **follow multiple links or perform multiple searches** if necessary to get complete information.
11. **CRITICAL**: At the end of your response, include a "Sources" section listing ALL URLs that were useful in answering the question.

---

## 💡 Best Practices & Search Strategies for Agents

### 🎯 Search Strategies
When searching for information, follow this structured strategy:

1. **Break down complex questions** - If the user's question has multiple parts, search for each part separately.
2. **Use specific, targeted queries** - Prefer multiple small, focused searches (3-6 words) over one broad search.
   - *Bad*: "Python 3.12 new features performance improvements async changes"
   - *Good*: First `ddgo-search text "Python 3.12 new features"`, then `ddgo-search text "Python 3.12 performance improvements"`, then `ddgo-search text "Python 3.12 async changes"`
3. **Iterate and refine** - If initial results aren't helpful, try different search terms or more specific queries.
4. **Search for different aspects** - For comprehensive answers, search for different angles of the topic.
5. **Follow up on promising results** - When you find a good source, fetch it using `ddgo-search fetch` and look for links to related information.

#### Example Workflow
To answer: *"What are the pros and cons of using Rust vs Go for web services?"*:
- **Search 1**: `ddgo-search text "Rust web services advantages"`
- **Search 2**: `ddgo-search text "Go web services advantages"`
- **Search 3**: `ddgo-search text "Rust vs Go performance comparison"`
- **Search 4**: `ddgo-search text "Rust vs Go developer experience"`
- **Fetch**: Fetch the most relevant results from each search using `ddgo-search fetch <URL>`.

### 🛡️ Resiliency & Efficiency

1. **Token Conservation**:
   - Use `--format plain` (default) or `--format table` instead of `json` or `csv` when listing results in a terminal. The `plain` format is the most token-efficient representation, whereas the custom `table` format auto-wraps content to fit terminal widths cleanly without truncation.
   - For `fetch` or `extract`, use the defaults to get Markdown representation which is easier to comprehend. Adjust `--max-size` if you want to retrieve smaller chunks of a page to keep tokens under control.

2. **Handling Rate Limits**:
   - The CLI has built-in global process-safe rate limiting that enforces a random delay (1.5s - 3.0s) between successive requests across all processes.
   - If you encounter rate limit issues, the CLI will automatically backoff. You do not need to build manual retry loops around CLI invocations; just configure `--max-retries` and provide reliable proxies if querying heavily.

3. **Proxy Rotation**:
   - For high-volume searching, always supply a list of proxies:
     ```bash
     ddgo-search -p "proxy1,proxy2,proxy3" text "query"
     # Or point to a file containing proxies (one per line)
     ddgo-search -p "proxies.txt" text "query"
     ```
   - The CLI rotates to the next proxy server automatically on failure.

