---
name: ddgo-search-skill
description: Performs web search queries (text, images, videos, news, books), extracts webpage summaries, or directly fetches/converts webpages into clean plain text, markdown, or HTML via the ddgo-search CLI wrapper. Use when searching the web, retrieving search results, fetching or scraping web content, or using DuckDuckGo search.
dependencies: python>=3.11
allowed-tools:
  - Bash
---

# DDGo Search Skill

`ddgo-search` is a resilient, token-efficient CLI wrapper around the DuckDuckGo Search (`ddgs`) Python library. It provides robust rate-limiting, proxy rotation, webpage extraction, and direct content fetching.

## 🚀 Quick Start

Run commands using `uv run ddgo-search`:

```bash
# Text search (default format is ASCII table)
uv run ddgo-search text "artificial intelligence"

# Direct URL fetch and convert to Markdown
uv run ddgo-search fetch "https://example.com" --format markdown
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
uv run ddgo-search -p "http://proxy.example.com:8080" -t 15 text "latest technology"
```

### Subcommands

#### 1. Text Search (`text`)
Search the web for text results.
```bash
uv run ddgo-search text "python programming" [OPTIONS]
```
- `--max-results INTEGER`: Maximum results to return (default: `10`).
- `--timelimit [d|w|m|y]`: Limit results to day, week, month, or year.
- `-f, --format [table|plain|json|csv]`: Output format (default: `table`).

#### 2. Image Search (`images`)
Search for images.
```bash
uv run ddgo-search images "space nebula" [OPTIONS]
```
- `--size [Small|Medium|Large|Wallpaper]`
- `--color [color|Monochrome|red|green|etc.]`
- `--type-image [photo|clipart|gif|transparent|line]`
- `--layout [Square|Tall|Wide]`
- `--license-image [any|Public|Share|Modify]`
- `-f, --format [table|plain|json|csv]` (default: `table`).

#### 3. Video Search (`videos`)
Search for videos.
```bash
uv run ddgo-search videos "rust tutorial" [OPTIONS]
```
- `--resolution [high|standard]`
- `--duration [short|medium|long]`
- `--license-videos [creativeCommon|youtube]`
- `-f, --format [table|plain|json|csv]` (default: `table`).

*Note: The underlying library standard resolution expects `"standart"`. The CLI enum maps `"standard"` to `"standart"` automatically.*

#### 4. News Search (`news`)
Query recent news.
```bash
uv run ddgo-search news "climate change" [OPTIONS]
```
- `--timelimit [d|w|m]`
- `-f, --format [table|plain|json|csv]` (default: `table`).

#### 5. Book Search (`books`)
Search DuckDuckGo books.
```bash
uv run ddgo-search books "machine learning" [OPTIONS]
```
- `--max-results INTEGER`: (default: `10`).
- `-f, --format [table|plain|json|csv]` (default: `table`).

#### 6. Web Page Extract (`extract`)
Extract main content using DuckDuckGo's internal extraction backend.
```bash
uv run ddgo-search extract "https://example.com" [OPTIONS]
```
- `-f, --format [text_markdown|text_plain|text_rich|text]` (default: `text_markdown`).
- `-o, --output PATH`: Save extracted content to file instead of printing.

#### 7. Direct Web Page Fetch (`fetch`)
Directly fetch a URL using `httpx` and convert its HTML content to Markdown, clean text, or raw HTML. **This is highly recommended for scraping specific pages bypasses DDG's extract servers.**
```bash
uv run ddgo-search fetch "https://example.com" [OPTIONS]
```
- `-f, --format [markdown|text|html]` (default: `markdown`).
- `-s, --max-size INTEGER`: Maximum content size in bytes before truncation to preserve tokens (default: `102400` / 100KB).
- `-o, --output PATH`: Save content to file instead of printing.

---

## 💡 Best Practices for Agents

1. **Token Conservation**:
   - Use `--format table` (default) or `--format plain` instead of `json` or `csv` when listing results in a terminal. The `table` format produces custom space-padded ASCII borders to save context window tokens compared to standard heavy grids.
   - For `fetch` or `extract`, use the defaults to get Markdown representation which is easier to comprehend. Adjust `--max-size` if you want to retrieve smaller chunks of a page to keep tokens under control.

2. **Handling Rate Limits**:
   - The CLI has built-in global process-safe rate limiting that enforces a random delay (1.5s - 3.0s) between successive requests across all processes.
   - If you encounter rate limit issues, the CLI will automatically backoff. You do not need to build manual retry loops around CLI invocations; just configure `--max-retries` and provide reliable proxies if querying heavily.

3. **Proxy Rotation**:
   - For high-volume searching, always supply a list of proxies:
     ```bash
     uv run ddgo-search -p "proxy1,proxy2,proxy3" text "query"
     # Or point to a file containing proxies (one per line)
     uv run ddgo-search -p "proxies.txt" text "query"
     ```
   - The CLI rotates to the next proxy server automatically on failure.
