"""Search engine abstractions and fallback orchestration for ddgo-search."""

from typing import Any, List, Optional, Protocol
from .models import TextSearchResult


class TextSearchEngine(Protocol):
    """Protocol defining the interface for a text search engine."""

    def search(
        self,
        query: str,
        region: str = "us-en",
        safesearch: str = "moderate",
        timelimit: Optional[str] = None,
        max_results: Optional[int] = 10,
        page: int = 1,
        backend: str = "auto",
    ) -> List[TextSearchResult]:
        """Perform text search and return normalized results."""
        ...


class PrimaryTextSearchEngine:
    """Primary search engine wrapping the standard ddgs client SDK."""

    def __init__(self, adapter: Any) -> None:
        self.adapter = adapter

    def search(
        self,
        query: str,
        region: str = "us-en",
        safesearch: str = "moderate",
        timelimit: Optional[str] = None,
        max_results: Optional[int] = 10,
        page: int = 1,
        backend: str = "auto",
    ) -> List[TextSearchResult]:
        client = self.adapter._client
        if client is None:
            from .exceptions import SearchError

            raise SearchError(
                "Client is not initialized. Use inside a context manager."
            )

        def run() -> Any:
            return client.text(
                query=query,
                region=region,
                safesearch=safesearch,
                timelimit=timelimit,
                max_results=max_results,
                page=page,
                backend=backend,
            )

        raw_results = self.adapter._run_with_exception_mapping(run)
        results: List[TextSearchResult] = []
        for r in raw_results or []:
            results.append(
                TextSearchResult(
                    title=r.get("title", ""),
                    url=r.get("href", ""),
                    body=r.get("body", ""),
                )
            )
        return results


class FallbackTextSearchEngine:
    """Fallback search engine crawling JS-free DuckDuckGo Lite."""

    def __init__(
        self,
        proxy: Optional[str] = None,
        timeout: float = 10.0,
        verify: bool = True,
    ) -> None:
        self.proxy = proxy
        self.timeout = timeout
        self.verify = verify

    def search(
        self,
        query: str,
        region: str = "us-en",
        safesearch: str = "moderate",
        timelimit: Optional[str] = None,
        max_results: Optional[int] = 10,
        page: int = 1,
        backend: str = "auto",
    ) -> List[TextSearchResult]:
        from .utils import scrape_ddg_lite

        fallback_results = scrape_ddg_lite(
            query=query,
            region=region,
            safesearch=safesearch,
            timelimit=timelimit,
            max_results=max_results,
            proxy=self.proxy,
            timeout=self.timeout,
            verify=self.verify,
        )
        results: List[TextSearchResult] = []
        for r in fallback_results:
            results.append(
                TextSearchResult(
                    title=r.get("title", ""),
                    url=r.get("url", ""),
                    body=r.get("body", ""),
                )
            )
        return results


class OrchestratedTextSearchEngine:
    """Orchestrator coordinating primary and fallback search engines."""

    def __init__(
        self,
        primary: TextSearchEngine,
        fallback: TextSearchEngine,
    ) -> None:
        self.primary = primary
        self.fallback = fallback

    def search(
        self,
        query: str,
        region: str = "us-en",
        safesearch: str = "moderate",
        timelimit: Optional[str] = None,
        max_results: Optional[int] = 10,
        page: int = 1,
        backend: str = "auto",
    ) -> List[TextSearchResult]:
        try:
            return self.primary.search(
                query=query,
                region=region,
                safesearch=safesearch,
                timelimit=timelimit,
                max_results=max_results,
                page=page,
                backend=backend,
            )
        except Exception as e:
            from .utils import err_console

            err_console.print(
                f"[yellow]Warning: Primary DDG search failed ({e}). "
                f"Falling back to self-developed Lite search crawler...[/yellow]"
            )
            try:
                return self.fallback.search(
                    query=query,
                    region=region,
                    safesearch=safesearch,
                    timelimit=timelimit,
                    max_results=max_results,
                    page=page,
                    backend=backend,
                )
            except Exception as fallback_err:
                from .exceptions import SearchError

                raise SearchError(
                    f"Search failed on both primary and fallback engines. "
                    f"Primary error: {e}. Fallback error: {fallback_err}"
                ) from fallback_err
