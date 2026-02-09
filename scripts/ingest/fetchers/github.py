"""GitHub repository rule fetcher."""

from __future__ import annotations

import fnmatch
import logging
import time
from typing import Any

import requests

from scripts.ingest.fetchers import BaseFetcher, FetchError

logger = logging.getLogger(__name__)

GITHUB_RAW_BASE = "https://raw.githubusercontent.com"
GITHUB_API_BASE = "https://api.github.com"
DEFAULT_TIMEOUT = 30


class GitHubFetcher(BaseFetcher):
    """Fetches rule definitions from GitHub repositories."""

    def fetch(self, etag: str | None = None, last_modified: str | None = None) -> dict[str, Any]:
        """Fetch rule files from a GitHub repository."""
        # Parse owner/repo from URL
        # Expected format: https://github.com/owner/repo
        parts = self.url.rstrip("/").split("/")
        if len(parts) < 5 or parts[2] != "github.com":
            raise FetchError(
                f"Invalid GitHub URL format: {self.url}",
                source_id=self.source_id,
            )

        owner = parts[3]
        repo = parts[4]
        branch = self.fetch_config.get("branch", "main")
        rules_path = self.fetch_config.get("rules_path", "")
        file_pattern = self.fetch_config.get("file_pattern", "*.py")

        # Use GitHub API to list files in the rules directory
        api_url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "aws-misconfig-db-ingest/1.0",
        }
        if etag:
            headers["If-None-Match"] = etag

        try:
            response = requests.get(api_url, headers=headers, timeout=DEFAULT_TIMEOUT)
        except requests.RequestException as e:
            raise FetchError(
                f"Failed to fetch GitHub tree: {e}",
                source_id=self.source_id,
            ) from e

        if response.status_code == 304:
            return {
                "content": None,
                "etag": etag,
                "last_modified": last_modified,
                "not_modified": True,
            }

        if response.status_code != 200:
            raise FetchError(
                f"GitHub API returned {response.status_code}",
                source_id=self.source_id,
                status_code=response.status_code,
            )

        tree = response.json()

        # Filter to matching files
        matching_files = []
        for item in tree.get("tree", []):
            if item["type"] != "blob":
                continue
            path = item["path"]
            if rules_path and not path.startswith(rules_path):
                continue
            if fnmatch.fnmatch(path.split("/")[-1], file_pattern):
                matching_files.append(path)

        # Fetch file contents (with rate limiting)
        max_files = self.fetch_config.get("max_files", 50)
        file_contents = []
        for filepath in matching_files[:max_files]:
            raw_url = f"{GITHUB_RAW_BASE}/{owner}/{repo}/{branch}/{filepath}"
            try:
                resp = requests.get(raw_url, timeout=DEFAULT_TIMEOUT, headers={"User-Agent": "aws-misconfig-db-ingest/1.0"})
                resp.raise_for_status()
                file_contents.append({
                    "path": filepath,
                    "content": resp.text,
                    "url": f"https://github.com/{owner}/{repo}/blob/{branch}/{filepath}",
                })
                time.sleep(0.2)  # Rate limiting
            except requests.RequestException as e:
                logger.warning("Failed to fetch %s: %s", filepath, e)

        return {
            "content": file_contents,
            "etag": response.headers.get("ETag"),
            "last_modified": response.headers.get("Last-Modified"),
            "not_modified": False,
        }
