"""Tests for fetcher modules."""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.ingest.fetchers import BaseFetcher, FetchError
from scripts.ingest.fetchers.rss import RSSFetcher
from scripts.ingest.fetchers.html import HTMLFetcher
from scripts.ingest.fetchers.github import GitHubFetcher


class TestFetchError:
    def test_basic(self):
        err = FetchError("test error")
        assert str(err) == "test error"

    def test_with_source_id(self):
        err = FetchError("fail", source_id="src-1", status_code=404)
        assert err.source_id == "src-1"
        assert err.status_code == 404


class TestRSSFetcher:
    def _make_fetcher(self):
        return RSSFetcher({
            "id": "test-rss",
            "name": "Test RSS",
            "type": "rss",
            "url": "https://example.com/feed",
            "fetch_config": {"max_items": 5},
        })

    @patch("scripts.ingest.fetchers.rss.feedparser")
    def test_fetch_success(self, mock_fp):
        mock_fp.parse.return_value = MagicMock(
            status=200,
            entries=[{"title": f"Item {i}"} for i in range(10)],
            bozo=False,
            get=lambda k, d=None: {"etag": "new-etag", "modified": "new-mod"}.get(k, d),
        )

        fetcher = self._make_fetcher()
        result = fetcher.fetch()

        assert not result["not_modified"]
        assert len(result["content"]) == 5  # max_items cap

    @patch("scripts.ingest.fetchers.rss.feedparser")
    def test_fetch_304(self, mock_fp):
        feed_result = MagicMock(entries=[], bozo=False)
        feed_result.get = lambda k, d=None: {"status": 304}.get(k, d)
        mock_fp.parse.return_value = feed_result

        fetcher = self._make_fetcher()
        result = fetcher.fetch(etag="old-etag")

        assert result["not_modified"]
        assert result["content"] is None

    @patch("scripts.ingest.fetchers.rss.feedparser")
    def test_fetch_http_error(self, mock_fp):
        feed_result = MagicMock(entries=[], bozo=False)
        feed_result.get = lambda k, d=None: {"status": 500}.get(k, d)
        mock_fp.parse.return_value = feed_result

        fetcher = self._make_fetcher()
        with pytest.raises(FetchError, match="HTTP 500"):
            fetcher.fetch()


class TestHTMLFetcher:
    def _make_fetcher(self):
        return HTMLFetcher({
            "id": "test-html",
            "name": "Test HTML",
            "type": "html",
            "url": "https://example.com/docs",
            "fetch_config": {},
        })

    @patch("scripts.ingest.fetchers.html.requests")
    def test_fetch_success(self, mock_requests):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "<html><body><h2>Test</h2><p>Content here</p></body></html>"
        mock_resp.content = b"x" * 200
        mock_resp.headers = {"ETag": "etag-1"}
        mock_requests.get.return_value = mock_resp

        fetcher = self._make_fetcher()
        result = fetcher.fetch()

        assert not result["not_modified"]
        assert len(result["content"]) >= 1

    @patch("scripts.ingest.fetchers.html.requests")
    def test_fetch_304(self, mock_requests):
        mock_resp = MagicMock()
        mock_resp.status_code = 304
        mock_resp.raise_for_status = MagicMock()
        mock_requests.get.return_value = mock_resp

        fetcher = self._make_fetcher()
        result = fetcher.fetch(etag="old")
        assert result["not_modified"]

    @patch("scripts.ingest.fetchers.html.requests")
    def test_fetch_empty_response(self, mock_requests):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = b"x"
        mock_resp.raise_for_status = MagicMock()
        mock_requests.get.return_value = mock_resp

        fetcher = self._make_fetcher()
        with pytest.raises(FetchError, match="Empty response"):
            fetcher.fetch()


class TestGitHubFetcher:
    def _make_fetcher(self):
        return GitHubFetcher({
            "id": "test-github",
            "name": "Test GitHub",
            "type": "github",
            "url": "https://github.com/test/repo",
            "fetch_config": {"branch": "main", "rules_path": "rules/", "file_pattern": "*.py", "max_files": 2},
        })

    @patch("scripts.ingest.fetchers.github.requests")
    def test_fetch_success(self, mock_requests):
        tree_resp = MagicMock()
        tree_resp.status_code = 200
        tree_resp.json.return_value = {
            "tree": [
                {"type": "blob", "path": "rules/check1.py"},
                {"type": "blob", "path": "rules/check2.py"},
                {"type": "blob", "path": "other/not_matched.py"},
            ]
        }
        tree_resp.headers = {"ETag": "tree-etag"}

        file_resp = MagicMock()
        file_resp.text = "# check content"
        file_resp.raise_for_status = MagicMock()

        mock_requests.get.side_effect = [tree_resp, file_resp, file_resp]

        fetcher = self._make_fetcher()
        result = fetcher.fetch()

        assert not result["not_modified"]
        assert len(result["content"]) == 2

    def test_invalid_github_url(self):
        fetcher = GitHubFetcher({
            "id": "bad",
            "name": "Bad",
            "type": "github",
            "url": "https://not-github.com/repo",
            "fetch_config": {},
        })
        with pytest.raises(FetchError, match="Invalid GitHub URL"):
            fetcher.fetch()
