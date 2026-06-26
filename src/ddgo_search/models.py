"""Domain models and data transfer objects for ddgo-search."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, slots=True)
class TextSearchResult:
    """Normalized DTO for text search results."""

    title: str
    url: str
    body: str


@dataclass(frozen=True, slots=True)
class ImageSearchResult:
    """Normalized DTO for image search results."""

    title: str
    url: str
    source: str
    width: Optional[int] = None
    height: Optional[int] = None


@dataclass(frozen=True, slots=True)
class VideoSearchResult:
    """Normalized DTO for video search results."""

    title: str
    duration: str
    publisher: str
    published: str
    url: str


@dataclass(frozen=True, slots=True)
class NewsSearchResult:
    """Normalized DTO for news search results."""

    date: str
    title: str
    source: str
    url: str
    body: str


@dataclass(frozen=True, slots=True)
class BookSearchResult:
    """Normalized DTO for book search results."""

    title: str
    author: str
    publisher: str
    info: str
    url: str


@dataclass(frozen=True, slots=True)
class ExtractResult:
    """Normalized DTO for extracted webpage content."""

    url: str
    content: str
