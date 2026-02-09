"""HTML documentation page parser."""

from __future__ import annotations

import logging
import re
from typing import Any

from scripts.ingest import RawItem
from scripts.ingest.parsers import BaseParser

logger = logging.getLogger(__name__)


class HTMLParser(BaseParser):
    """Parses HTML documentation pages into RawItems."""

    def parse(self, raw_content: Any) -> list[RawItem]:
        """Parse BeautifulSoup page objects into RawItems."""
        if raw_content is None:
            return []

        items = []
        for page in raw_content:
            try:
                page_items = self._parse_page(page)
                items.extend(page_items)
            except Exception as e:
                logger.warning("Failed to parse HTML page %s: %s", page.get("url", ""), e)

        logger.info("Source %s: parsed %d items from %d pages", self.source_id, len(items), len(raw_content))
        return items

    def _parse_page(self, page: dict) -> list[RawItem]:
        """Parse a single HTML page into items."""
        soup = page["soup"]
        url = page["url"]
        items = []

        item_selector = self.parse_config.get("item_selector")
        title_selector = self.parse_config.get("title_selector", "h2, h3")
        body_selector = self.parse_config.get("body_selector")

        if item_selector:
            # Structured extraction using CSS selectors
            elements = soup.select(item_selector)
            for elem in elements:
                title_elem = elem.select_one(title_selector) if title_selector else None
                title = title_elem.get_text(strip=True) if title_elem else ""

                if body_selector:
                    body_elem = elem.select_one(body_selector)
                    body = body_elem.get_text(strip=True) if body_elem else elem.get_text(strip=True)
                else:
                    body = elem.get_text(strip=True)

                if title and len(body) >= 20:
                    items.append(RawItem(
                        source_id=self.source_id,
                        source_name=self.source_name,
                        title=title,
                        body=body,
                        url=url,
                        categories=list(self.categories),
                        raw_metadata={"page_url": url},
                    ))
        else:
            # Fallback: extract sections by headers
            items.extend(self._extract_sections(soup, url))

        return items

    def _extract_sections(self, soup, url: str) -> list[RawItem]:
        """Extract sections from page using header elements."""
        items = []
        headers = soup.find_all(re.compile(r"^h[2-4]$"))

        for header in headers:
            title = header.get_text(strip=True)
            if not title or len(title) < 5:
                continue

            # Collect text from siblings until next header
            body_parts = []
            sibling = header.find_next_sibling()
            while sibling and (not sibling.name or not re.match(r"^h[1-4]$", sibling.name or "")):
                if sibling.name:
                    text = sibling.get_text(strip=True)
                    if text:
                        body_parts.append(text)
                sibling = sibling.find_next_sibling() if sibling else None

            body = " ".join(body_parts)
            if len(body) >= 50:
                items.append(RawItem(
                    source_id=self.source_id,
                    source_name=self.source_name,
                    title=title,
                    body=body[:4000],  # Cap body length
                    url=url,
                    categories=list(self.categories),
                    raw_metadata={"page_url": url, "header_level": header.name},
                ))

        return items
