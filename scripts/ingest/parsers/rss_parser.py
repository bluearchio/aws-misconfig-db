"""RSS/Atom feed content parser."""

from __future__ import annotations

import html
import logging
import re
import time
from datetime import datetime, timezone
from typing import Any

from scripts.ingest import RawItem
from scripts.ingest.parsers import BaseParser

logger = logging.getLogger(__name__)


def strip_html(text: str) -> str:
    """Remove HTML tags and decode entities."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


class RSSParser(BaseParser):
    """Parses RSS/Atom feed entries into RawItems."""

    def parse(self, raw_content: Any) -> list[RawItem]:
        """Parse feedparser entries into RawItems."""
        if raw_content is None:
            return []

        items = []
        for entry in raw_content:
            try:
                item = self._parse_entry(entry)
                if item:
                    items.append(item)
            except Exception as e:
                logger.warning("Failed to parse RSS entry: %s", e)

        logger.info("Source %s: parsed %d items from %d entries", self.source_id, len(items), len(raw_content))
        return items

    def _parse_entry(self, entry: dict) -> RawItem | None:
        """Parse a single feedparser entry."""
        title = entry.get("title", "").strip()
        if not title:
            return None

        # Extract body from summary or content
        body = ""
        if entry.get("content"):
            body = entry["content"][0].get("value", "")
        elif entry.get("summary"):
            body = entry["summary"]

        body = strip_html(body)

        # Skip entries with no meaningful content
        if len(body) < 50:
            logger.debug("Skipping entry with short body: %s", title)
            return None

        # Extract URL
        url = entry.get("link", "")

        # Extract published date
        published_at = None
        if entry.get("published_parsed"):
            try:
                ts = time.mktime(entry["published_parsed"])
                published_at = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            except (ValueError, OverflowError):
                pass

        return RawItem(
            source_id=self.source_id,
            source_name=self.source_name,
            title=title,
            body=body,
            url=url,
            published_at=published_at,
            categories=list(self.categories),
            raw_metadata={
                "tags": [t.get("term", "") for t in entry.get("tags", [])],
                "author": entry.get("author", ""),
            },
        )
