"""HTML page fetcher."""

from __future__ import annotations

import logging
import re
import time
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from scripts.ingest.fetchers import BaseFetcher, FetchError

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30
MAX_RETRIES = 2
RETRY_DELAY = 5


class HTMLFetcher(BaseFetcher):
    """Fetches and parses HTML documentation pages."""

    def fetch(self, etag: str | None = None, last_modified: str | None = None) -> dict[str, Any]:
        """Fetch HTML page with optional conditional request headers."""
        headers = {"User-Agent": "aws-misconfig-db-ingest/1.0"}
        if etag:
            headers["If-None-Match"] = etag
        if last_modified:
            headers["If-Modified-Since"] = last_modified

        response = self._fetch_with_retry(self.url, headers)

        if response.status_code == 304:
            logger.info("Source %s: not modified (304)", self.source_id)
            return {
                "content": None,
                "etag": etag,
                "last_modified": last_modified,
                "not_modified": True,
            }

        if len(response.content) < 100:
            raise FetchError(
                f"Empty response from {self.url} ({len(response.content)} bytes)",
                source_id=self.source_id,
                status_code=response.status_code,
            )

        soup = BeautifulSoup(response.text, "lxml")
        pages = [{"url": self.url, "soup": soup}]

        # Follow links if configured
        if self.fetch_config.get("follow_links"):
            link_pattern = self.fetch_config.get("link_pattern", "")
            pages.extend(self._follow_links(soup, link_pattern))

        return {
            "content": pages,
            "etag": response.headers.get("ETag"),
            "last_modified": response.headers.get("Last-Modified"),
            "not_modified": False,
        }

    def _fetch_with_retry(self, url: str, headers: dict) -> requests.Response:
        """Fetch URL with retry logic."""
        last_error = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                response = requests.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                last_error = e
                if attempt < MAX_RETRIES:
                    logger.warning("Retry %d for %s: %s", attempt + 1, url, e)
                    time.sleep(RETRY_DELAY)

        raise FetchError(
            f"Failed after {MAX_RETRIES + 1} attempts: {last_error}",
            source_id=self.source_id,
            status_code=getattr(last_error, "response", None) and last_error.response.status_code,
        )

    def _follow_links(self, soup: BeautifulSoup, link_pattern: str) -> list[dict]:
        """Follow links matching pattern and fetch those pages."""
        pages = []
        if not link_pattern:
            return pages

        pattern = re.compile(link_pattern)
        seen_urls = {self.url}
        max_pages = self.fetch_config.get("max_pages", 20)

        for a_tag in soup.find_all("a", href=True):
            if len(pages) >= max_pages:
                break

            href = urljoin(self.url, a_tag["href"])
            if href in seen_urls:
                continue
            if not pattern.search(href):
                continue

            seen_urls.add(href)
            try:
                headers = {"User-Agent": "aws-misconfig-db-ingest/1.0"}
                resp = requests.get(href, headers=headers, timeout=DEFAULT_TIMEOUT)
                resp.raise_for_status()
                child_soup = BeautifulSoup(resp.text, "lxml")
                pages.append({"url": href, "soup": child_soup})
                logger.debug("Followed link: %s", href)
                time.sleep(0.5)  # Be polite
            except requests.RequestException as e:
                logger.warning("Failed to follow link %s: %s", href, e)

        return pages
