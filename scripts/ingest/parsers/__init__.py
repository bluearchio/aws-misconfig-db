"""Base parser interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from scripts.ingest import RawItem


class BaseParser(ABC):
    """Abstract base class for source content parsers."""

    def __init__(self, source_config: dict[str, Any]):
        self.source_config = source_config
        self.source_id = source_config["id"]
        self.source_name = source_config["name"]
        self.categories = source_config.get("categories", [])
        self.parse_config = source_config.get("parse_config", {})

    @abstractmethod
    def parse(self, raw_content: Any) -> list[RawItem]:
        """
        Parse raw fetched content into a list of RawItems.

        Args:
            raw_content: The "content" value from a fetcher's response

        Returns:
            List of RawItem objects ready for deduplication
        """
        ...
