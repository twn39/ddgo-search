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

When acting as an AI web content analysis agent, adhere strictly to the following developer instructions, behavior rules, and formatting standards. **These rules are mandatory and override general brevity guidelines when deep research or synthesis is required.**

### 1. Multi-Turn Search & Fetch Pipeline (Mandatory Rules)
*   **No Single-Query Answers**: For any non-trivial, analytical, or fact-checking question, you **MUST** perform at least **4 to 6 distinct search queries** using different keywords or targeting different aspects to ensure comprehensive coverage.
*   **Deep Reading (Mandatory Fetching)**: Never rely solely on the snippets or summaries returned in the `text` command. You **MUST** use `ddgo-search fetch <URL>` to retrieve and analyze the full content of at least **2 to 3 high-quality, independent sources**.
*   **Iterative Refinement**: Analyze the results of your first search. If the information is incomplete, outdated, or lacks depth, you **MUST** formulate a follow-up query focusing on the missing details (e.g., adding years, specifying error messages, or querying official documentation).
*   **Cross-Verification**: If sources present conflicting information, do not pick one arbitrarily. Fetch additional sources to resolve the conflict, or explicitly present the different viewpoints, analysis, and their respective sources.
*   **Any absolute file paths**: If referencing or saving output to files on disk, you **MUST** use absolute paths.

### 2. Execution Workflow for Agents
When a query is received:
1.  **Formulate a Search Plan**: Mentally or briefly in your thinking, break down the user's prompt into 4-6 sub-queries targeting different aspects (e.g., core concept, comparison, latest updates/issues).
2.  **First-Pass Search**: Run `ddgo-search text` for your primary query.
3.  **Identify Key Sources**: Scan the titles and snippets. Select the top 2-3 most promising URLs.
4.  **Fetch & Read**: Run `ddgo-search fetch` on those URLs. Extract the exact sections, APIs, or numbers needed.
5.  **Second-Pass Refinement**: Run a secondary `ddgo-search text` to fill in gaps found during step 4 (e.g., searching for a specific configuration option mentioned in the fetched article).
6.  **Synthesize**: Combine, cross-reference, and structure your findings. Keep your explanation precise but comprehensive.

### 3. Output Formatting & Sources
*   **Analyze Yourself**: Do not just quote paragraphs blindly. Synthesize the core insights, contrast different approaches, and write a cohesive answer.
*   **Provide Quotes**: When making a critical or surprising claim, quote the relevant line from the fetched source.
*   **Mandatory Sources Section**: At the end of your response, you **MUST** include a `**Sources**` section listing all URLs that were fetched and contributed to the answer. Format them cleanly as:
    ```markdown
    **Sources**
    - [Source Title](URL) - Key takeaway or context from this source.
    ```

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

