"""Tests for config module."""

import json
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.ingest.config import load_sources, validate_config, get_enabled_sources, REQUIRED_SOURCE_FIELDS


class TestValidateConfig:
    def test_valid_config(self, sample_source_config):
        """Valid config should not raise."""
        errors = validate_config(sample_source_config)
        assert errors == []

    def test_missing_version(self):
        config = {"sources": []}
        with pytest.raises(ValueError, match="Missing 'version'"):
            validate_config(config)

    def test_missing_sources(self):
        config = {"version": "1.0.0"}
        with pytest.raises(ValueError, match="Missing 'sources'"):
            validate_config(config)

    def test_sources_not_list(self):
        config = {"version": "1.0.0", "sources": "not-a-list"}
        with pytest.raises(ValueError, match="must be a list"):
            validate_config(config)

    def test_duplicate_ids(self):
        config = {
            "version": "1.0.0",
            "sources": [
                {"id": "dup", "name": "Dup1", "type": "rss", "url": "http://x", "categories": ["security"], "enabled": True},
                {"id": "dup", "name": "Dup2", "type": "rss", "url": "http://y", "categories": ["cost"], "enabled": True},
            ]
        }
        with pytest.raises(ValueError, match="duplicate id"):
            validate_config(config)

    def test_invalid_source_type(self):
        config = {
            "version": "1.0.0",
            "sources": [
                {"id": "bad", "name": "Bad", "type": "ftp", "url": "ftp://x", "categories": ["security"], "enabled": True}
            ]
        }
        with pytest.raises(ValueError, match="invalid type"):
            validate_config(config)

    def test_missing_required_fields(self):
        config = {
            "version": "1.0.0",
            "sources": [
                {"id": "incomplete"}
            ]
        }
        with pytest.raises(ValueError, match="missing fields"):
            validate_config(config)

    def test_empty_categories(self):
        config = {
            "version": "1.0.0",
            "sources": [
                {"id": "bad", "name": "Bad", "type": "rss", "url": "http://x", "categories": [], "enabled": True}
            ]
        }
        with pytest.raises(ValueError, match="non-empty list"):
            validate_config(config)


class TestLoadSources:
    def test_load_from_file(self, tmp_path, sample_source_config):
        config_file = tmp_path / "sources.json"
        with open(config_file, "w") as f:
            json.dump(sample_source_config, f)

        config = load_sources(config_file)
        assert config["version"] == "1.0.0"
        assert len(config["sources"]) == 4

    def test_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_sources(tmp_path / "nonexistent.json")


class TestGetEnabledSources:
    def test_filters_disabled(self, sample_source_config):
        enabled = get_enabled_sources(sample_source_config)
        assert len(enabled) == 3
        assert all(s["enabled"] for s in enabled)

    def test_filter_by_type(self, sample_source_config):
        rss_sources = get_enabled_sources(sample_source_config, source_type="rss")
        assert len(rss_sources) == 1
        assert rss_sources[0]["type"] == "rss"

    def test_filter_by_ids(self, sample_source_config):
        sources = get_enabled_sources(sample_source_config, source_ids=["test-rss-source"])
        assert len(sources) == 1
        assert sources[0]["id"] == "test-rss-source"

    def test_filter_by_type_and_ids(self, sample_source_config):
        sources = get_enabled_sources(sample_source_config, source_type="html", source_ids=["test-html-source"])
        assert len(sources) == 1
