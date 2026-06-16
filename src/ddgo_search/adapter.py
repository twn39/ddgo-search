"""Adapter layer for the ddgs (DuckDuckGo Search) library to shield ddgo-search from SDK API changes."""

from typing import Any, Callable, List, Optional, TypedDict

from ddgs import DDGS
from ddgs.exceptions import DDGSException, TimeoutException

from .exceptions import SearchError, SearchTimeoutError


class TextSearchResult(TypedDict):
    """Normalized DTO for text search results."""

    title: str
    url: str
    body: str


class ImageSearchResult(TypedDict):
    """Normalized DTO for image search results."""

    title: str
    url: str
    source: str
    width: Optional[int]
    height: Optional[int]


class VideoSearchResult(TypedDict):
    """Normalized DTO for video search results."""

    title: str
    duration: str
    publisher: str
    published: str
    url: str


class NewsSearchResult(TypedDict):
    """Normalized DTO for news search results."""

    date: str
    title: str
    source: str
    url: str
    body: str


class BookSearchResult(TypedDict):
    """Normalized DTO for book search results."""

    title: str
    author: str
    publisher: str
    info: str
    url: str


class ExtractResult(TypedDict):
    """Normalized DTO for extracted webpage content."""

    url: str
    content: str


class DDGSAdapter:
    """Adapter wrapping ddgs.DDGS client, mapping parameters/exceptions and normalizing outputs."""

    def __init__(
        self,
        proxy: Optional[str] = None,
        timeout: int = 10,
        verify: bool = True,
    ) -> None:
        self.proxy = proxy
        self.timeout = timeout
        self.verify = verify
        self._client: Optional[Any] = None

    def __enter__(self) -> "DDGSAdapter":
        try:
            self._client = DDGS(
                proxy=self.proxy,
                timeout=self.timeout,
                verify=self.verify,
            )
            self._client.__enter__()
            return self
        except TimeoutException as e:
            raise SearchTimeoutError(f"Connection timeout: {e}") from e
        except DDGSException as e:
            raise SearchError(f"Connection error: {e}") from e
        except Exception as e:
            raise SearchError(f"Unexpected connection error: {e}") from e

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._client:
            try:
                self._client.__exit__(exc_type, exc_val, exc_tb)
            except TimeoutException as e:
                raise SearchTimeoutError(f"Timeout during teardown: {e}") from e
            except DDGSException as e:
                raise SearchError(f"Error during teardown: {e}") from e
            except Exception as e:
                raise SearchError(f"Unexpected error during teardown: {e}") from e
            finally:
                self._client = None

    def _run_with_exception_mapping(self, func: Callable[[], Any]) -> Any:
        try:
            return func()
        except TimeoutException as e:
            raise SearchTimeoutError(f"Search operation timed out: {e}") from e
        except DDGSException as e:
            raise SearchError(f"Search operation failed: {e}") from e
        except Exception as e:
            raise SearchError(f"Unexpected search error: {e}") from e

    def text(
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
        client = self._client
        if client is None:
            raise SearchError("Client is not initialized. Use inside a context manager.")

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

        raw_results = self._run_with_exception_mapping(run)
        results: List[TextSearchResult] = []
        for r in raw_results or []:
            results.append(
                {
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "body": r.get("body", ""),
                }
            )
        return results

    def images(
        self,
        query: str,
        region: str = "us-en",
        safesearch: str = "moderate",
        timelimit: Optional[str] = None,
        max_results: Optional[int] = 10,
        page: int = 1,
        backend: str = "auto",
        **kwargs: Any,
    ) -> List[ImageSearchResult]:
        """Perform image search and return normalized results."""
        client = self._client
        if client is None:
            raise SearchError("Client is not initialized. Use inside a context manager.")

        def run() -> Any:
            return client.images(
                query=query,
                region=region,
                safesearch=safesearch,
                timelimit=timelimit,
                max_results=max_results,
                page=page,
                backend=backend,
                **kwargs,
            )

        raw_results = self._run_with_exception_mapping(run)
        results: List[ImageSearchResult] = []
        for r in raw_results or []:
            results.append(
                {
                    "title": r.get("title", ""),
                    "url": r.get("image", ""),
                    "source": r.get("source", ""),
                    "width": r.get("width"),
                    "height": r.get("height"),
                }
            )
        return results

    def videos(
        self,
        query: str,
        region: str = "us-en",
        safesearch: str = "moderate",
        timelimit: Optional[str] = None,
        max_results: Optional[int] = 10,
        page: int = 1,
        backend: str = "auto",
        **kwargs: Any,
    ) -> List[VideoSearchResult]:
        """Perform video search and return normalized results."""
        client = self._client
        if client is None:
            raise SearchError("Client is not initialized. Use inside a context manager.")

        # Translate resolution 'standard' to 'standart' expected by the library
        if "resolution" in kwargs and kwargs["resolution"] == "standard":
            kwargs["resolution"] = "standart"

        def run() -> Any:
            return client.videos(
                query=query,
                region=region,
                safesearch=safesearch,
                timelimit=timelimit,
                max_results=max_results,
                page=page,
                backend=backend,
                **kwargs,
            )

        raw_results = self._run_with_exception_mapping(run)
        results: List[VideoSearchResult] = []
        for r in raw_results or []:
            results.append(
                {
                    "title": r.get("title", ""),
                    "duration": r.get("duration", ""),
                    "publisher": r.get("publisher", ""),
                    "published": r.get("published", ""),
                    "url": r.get("embed_url", r.get("url", "")),
                }
            )
        return results

    def news(
        self,
        query: str,
        region: str = "us-en",
        safesearch: str = "moderate",
        timelimit: Optional[str] = None,
        max_results: Optional[int] = 10,
        page: int = 1,
        backend: str = "auto",
    ) -> List[NewsSearchResult]:
        """Perform news search and return normalized results."""
        client = self._client
        if client is None:
            raise SearchError("Client is not initialized. Use inside a context manager.")

        def run() -> Any:
            return client.news(
                query=query,
                region=region,
                safesearch=safesearch,
                timelimit=timelimit,
                max_results=max_results,
                page=page,
                backend=backend,
            )

        raw_results = self._run_with_exception_mapping(run)
        results: List[NewsSearchResult] = []
        for r in raw_results or []:
            results.append(
                {
                    "date": r.get("date", ""),
                    "title": r.get("title", ""),
                    "source": r.get("source", ""),
                    "url": r.get("url", ""),
                    "body": r.get("body", ""),
                }
            )
        return results

    def books(
        self,
        query: str,
        max_results: Optional[int] = 10,
        page: int = 1,
        backend: str = "auto",
    ) -> List[BookSearchResult]:
        """Perform book search and return normalized results."""
        client = self._client
        if client is None:
            raise SearchError("Client is not initialized. Use inside a context manager.")

        def run() -> Any:
            return client.books(
                query=query,
                max_results=max_results,
                page=page,
                backend=backend,
            )

        raw_results = self._run_with_exception_mapping(run)
        results: List[BookSearchResult] = []
        for r in raw_results or []:
            results.append(
                {
                    "title": r.get("title", ""),
                    "author": r.get("author", ""),
                    "publisher": r.get("publisher", ""),
                    "info": r.get("info", ""),
                    "url": r.get("url", ""),
                }
            )
        return results

    def extract(
        self,
        url: str,
        fmt: str = "markdown",
    ) -> ExtractResult:
        """Fetch a URL and extract its main content as DTO."""
        client = self._client
        if client is None:
            raise SearchError("Client is not initialized. Use inside a context manager.")

        # Translate format to what the third-party client expects
        lib_fmt = fmt
        if fmt == "markdown":
            lib_fmt = "text_markdown"
        elif fmt == "plain":
            lib_fmt = "text_plain"
        elif fmt == "rich":
            lib_fmt = "text_rich"
        elif fmt == "html":
            lib_fmt = "text"

        def run() -> Any:
            return client.extract(
                url=url,
                fmt=lib_fmt,
            )

        r = self._run_with_exception_mapping(run)
        return {
            "url": r.get("url", url),
            "content": r.get("content", ""),
        }
