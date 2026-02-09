"""Tests for parser modules."""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.ingest import RawItem
from scripts.ingest.parsers.rss_parser import RSSParser, strip_html
from scripts.ingest.parsers.html_parser import HTMLParser
from scripts.ingest.parsers.github_parser import GitHubParser


class TestStripHtml:
    def test_removes_tags(self):
        assert strip_html("<p>Hello <b>world</b></p>") == "Hello world"

    def test_decodes_entities(self):
        assert strip_html("&amp; &lt;test&gt;") == "& <test>"

    def test_handles_empty(self):
        assert strip_html("") == ""
        assert strip_html(None) == ""


class TestRSSParser:
    def _make_parser(self):
        return RSSParser({
            "id": "test-rss",
            "name": "Test RSS",
            "type": "rss",
            "url": "https://example.com/feed",
            "categories": ["security"],
        })

    def test_parse_entries(self):
        parser = self._make_parser()
        entries = [
            {
                "title": "S3 Encryption Best Practices",
                "link": "https://example.com/s3",
                "summary": "A detailed guide about S3 encryption options and how to implement them for your buckets. " * 3,
                "published_parsed": (2026, 1, 15, 10, 0, 0, 2, 15, 0),
                "tags": [{"term": "S3"}, {"term": "Security"}],
                "author": "AWS",
            }
        ]

        items = parser.parse(entries)
        assert len(items) == 1
        assert items[0].source_id == "test-rss"
        assert items[0].title == "S3 Encryption Best Practices"
        assert items[0].categories == ["security"]
        assert items[0].content_hash  # Should be auto-computed

    def test_skips_short_body(self):
        parser = self._make_parser()
        entries = [{"title": "Short", "summary": "Too short"}]

        items = parser.parse(entries)
        assert len(items) == 0

    def test_skips_empty_title(self):
        parser = self._make_parser()
        entries = [{"title": "", "summary": "x" * 100}]

        items = parser.parse(entries)
        assert len(items) == 0

    def test_parse_none_content(self):
        parser = self._make_parser()
        assert parser.parse(None) == []

    def test_content_from_content_field(self):
        parser = self._make_parser()
        entries = [
            {
                "title": "Test Entry",
                "link": "https://example.com/test",
                "content": [{"value": "<p>This is the detailed content of the entry with enough text to pass the length check.</p>"}],
            }
        ]

        items = parser.parse(entries)
        assert len(items) == 1
        assert "detailed content" in items[0].body


class TestHTMLParser:
    def _make_parser(self, parse_config=None):
        return HTMLParser({
            "id": "test-html",
            "name": "Test HTML",
            "type": "html",
            "url": "https://example.com/docs",
            "categories": ["security"],
            "parse_config": parse_config or {},
        })

    def test_parse_with_selector(self):
        html = """
        <div class="rule-item">
            <h3>S3 bucket encryption check</h3>
            <p>This control verifies that S3 buckets have encryption enabled for data protection at rest.</p>
        </div>
        """
        parser = self._make_parser({"item_selector": ".rule-item", "title_selector": "h3"})
        soup = BeautifulSoup(html, "lxml")
        items = parser.parse([{"url": "https://example.com", "soup": soup}])

        assert len(items) == 1
        assert "encryption" in items[0].title.lower()

    def test_parse_fallback_sections(self):
        html = """
        <h2>S3 Security Best Practices</h2>
        <p>S3 buckets should always have encryption enabled. This is critical for data protection and compliance requirements across all workloads.</p>
        <h2>IAM Policy Management</h2>
        <p>IAM policies should follow least privilege. Review permissions regularly and use IAM Access Analyzer to identify unused permissions in your accounts.</p>
        """
        parser = self._make_parser()
        soup = BeautifulSoup(html, "lxml")
        items = parser.parse([{"url": "https://example.com", "soup": soup}])

        assert len(items) >= 1

    def test_parse_none_content(self):
        parser = self._make_parser()
        assert parser.parse(None) == []


class TestGitHubParser:
    def _make_parser(self):
        return GitHubParser({
            "id": "test-github",
            "name": "Test GitHub",
            "type": "github",
            "url": "https://github.com/test/repo",
            "categories": ["security"],
        })

    def test_parse_python_check(self):
        parser = self._make_parser()
        files = [{
            "path": "checks/s3_encryption.py",
            "content": '''
CheckID = "s3_encryption_check"
Description = "Ensure S3 buckets have encryption enabled"
Severity = "high"
ServiceName = "s3"

class s3_encryption_check:
    """Check that all S3 buckets have server-side encryption."""
    pass
''',
            "url": "https://github.com/test/repo/blob/main/checks/s3_encryption.py",
        }]

        items = parser.parse(files)
        assert len(items) == 1
        assert items[0].title == "s3_encryption_check"
        assert "high" in str(items[0].raw_metadata.get("severity", ""))

    def test_parse_yaml_rule(self):
        parser = self._make_parser()
        files = [{
            "path": "rules/s3_logging.yaml",
            "content": "name: s3_logging_check\ndescription: Ensure S3 logging is enabled\nseverity: medium",
            "url": "https://github.com/test/repo/blob/main/rules/s3_logging.yaml",
        }]

        items = parser.parse(files)
        assert len(items) == 1
        assert "s3_logging_check" in items[0].title

    def test_parse_skips_init_files(self):
        parser = self._make_parser()
        files = [{
            "path": "checks/__init__.py",
            "content": "# init",
            "url": "https://github.com/test/repo/blob/main/checks/__init__.py",
        }]

        items = parser.parse(files)
        assert len(items) == 0

    def test_parse_none_content(self):
        parser = self._make_parser()
        assert parser.parse(None) == []
