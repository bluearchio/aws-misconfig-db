"""Base fetcher interface and exceptions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class FetchError(Exception):
    """Raised when a fetch operation fails."""

    def __init__(self, message: str, source_id: str = "", status_code: int | None = None):
        self.source_id = source_id
        self.status_code = status_code
        super().__init__(message)


class BaseFetcher(ABC):
    """Abstract base class for source fetchers."""

    def __init__(self, source_config: dict[str, Any]):
        self.source_config = source_config
        self.source_id = source_config["id"]
        self.source_name = source_config["name"]
        self.url = source_config["url"]
        self.fetch_config = source_config.get("fetch_config", {})

    @abstractmethod
    def fetch(self, etag: str | None = None, last_modified: str | None = None) -> dict[str, Any]:
        """
        Fetch raw content from source.

        Args:
            etag: Previous ETag for conditional requests
            last_modified: Previous Last-Modified for conditional requests

        Returns:
            dict with keys:
                - "content": raw content (str, bytes, or parsed object)
                - "etag": new ETag header (or None)
                - "last_modified": new Last-Modified header (or None)
                - "not_modified": bool, True if 304 response
        """
        ...
