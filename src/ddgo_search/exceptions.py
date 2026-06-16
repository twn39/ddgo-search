"""Custom exceptions for ddgo-search application."""


class SearchError(Exception):
    """Base exception for search operations."""

    pass


class SearchTimeoutError(SearchError):
    """Exception raised when a search operation times out."""

    pass
