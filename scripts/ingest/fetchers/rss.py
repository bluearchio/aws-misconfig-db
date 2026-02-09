"""RSS/Atom feed fetcher."""

from __future__ import annotations

import logging
from typing import Any

import feedparser

from scripts.ingest.fetchers import BaseFetcher, FetchError

logger = logging.getLogger(__name__)


class RSSFetcher(BaseFetcher):
    """Fetches RSS/Atom feeds using feedparser."""

    def fetch(self, etag: str | None = None, last_modified: str | None = None) -> dict[str, Any]:
        """Fetch RSS feed, supporting conditional requests."""
        try:
            kwargs = {}
            if etag:
                kwargs["etag"] = etag
            if last_modified:
                kwargs["modified"] = last_modified

            feed = feedparser.parse(self.url, **kwargs)

            # Check for HTTP errors
            status = feed.get("status", 200)
            if status == 304:
                logger.info("Source %s: not modified (304)", self.source_id)
                return {
                    "content": None,
                    "etag": etag,
                    "last_modified": last_modified,
                    "not_modified": True,
                }

            if status >= 400:
                raise FetchError(
                    f"HTTP {status} fetching {self.url}",
                    source_id=self.source_id,
                    status_code=status,
                )

            if feed.bozo and not feed.entries:
                raise FetchError(
                    f"Feed parse error: {feed.bozo_exception}",
                    source_id=self.source_id,
                )

            # Apply max_items limit
            max_items = self.fetch_config.get("max_items", 50)
            entries = feed.entries[:max_items]

            return {
                "content": entries,
                "etag": feed.get("etag"),
                "last_modified": feed.get("modified"),
                "not_modified": False,
            }

        except FetchError:
            raise
        except Exception as e:
            raise FetchError(
                f"Failed to fetch RSS feed {self.url}: {e}",
                source_id=self.source_id,
            ) from e
