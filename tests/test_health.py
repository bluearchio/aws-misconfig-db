"""Tests for health check module."""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.ingest.health import run_health_checks, check_source_yields, check_stale_sources, check_staging_overflow, check_state_corruption


class TestCheckSourceYields:
    def test_no_warning_when_ok(self):
        state = {"sources": {"src1": {"consecutive_empty": 1}}}
        results = check_source_yields(state, {})
        assert all(r["severity"] == "OK" for r in results)

    def test_warns_after_3_empty(self):
        state = {"sources": {"src1": {"consecutive_empty": 3}}}
        results = check_source_yields(state, {})
        assert any(r["severity"] == "WARNING" for r in results)


class TestCheckStaleSources:
    def test_no_warning_for_recent(self):
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        state = {"sources": {"src1": {"last_fetched_at": now}}}
        config = {"sources": [{"id": "src1", "enabled": True}]}
        results = check_stale_sources(state, config)
        assert all(r["severity"] == "OK" for r in results)

    def test_warns_for_stale(self):
        state = {"sources": {"src1": {"last_fetched_at": "2020-01-01T00:00:00Z"}}}
        config = {"sources": [{"id": "src1", "enabled": True}]}
        results = check_stale_sources(state, config)
        assert any(r["severity"] == "WARNING" for r in results)

    def test_warns_for_never_fetched(self):
        state = {"sources": {}}
        config = {"sources": [{"id": "src1", "enabled": True}]}
        results = check_stale_sources(state, config)
        assert any(r["severity"] == "WARNING" for r in results)


class TestCheckStagingOverflow:
    def test_no_warning_when_ok(self, tmp_staging_dir):
        with patch("scripts.ingest.health.STAGING_DIR", tmp_staging_dir):
            results = check_staging_overflow()
        assert all(r["severity"] == "OK" for r in results)

    def test_warns_when_many(self, tmp_staging_dir):
        for i in range(101):
            (tmp_staging_dir / f"item-{i}.json").write_text("{}")

        with patch("scripts.ingest.health.STAGING_DIR", tmp_staging_dir):
            results = check_staging_overflow()
        assert any(r["severity"] == "WARNING" for r in results)


class TestCheckStateCorruption:
    def test_ok_when_valid(self, tmp_ingest_dir):
        import json
        state_file = tmp_ingest_dir / "state.json"
        with open(state_file, "w") as f:
            json.dump({"version": "1.0.0", "sources": {}, "runs": []}, f)

        with patch("scripts.ingest.health.STATE_FILE", state_file):
            results = check_state_corruption()
        assert all(r["severity"] == "OK" for r in results)

    def test_critical_when_corrupt(self, tmp_ingest_dir):
        state_file = tmp_ingest_dir / "state.json"
        state_file.write_text("not json{{{")

        with patch("scripts.ingest.health.STATE_FILE", state_file):
            results = check_state_corruption()
        assert any(r["severity"] == "CRITICAL" for r in results)


class TestRunHealthChecks:
    def test_runs_all_checks(self, tmp_ingest_dir, tmp_staging_dir):
        import json
        state_file = tmp_ingest_dir / "state.json"
        with open(state_file, "w") as f:
            json.dump({"version": "1.0.0", "sources": {}, "runs": []}, f)

        sources_file = tmp_ingest_dir / "sources.json"
        with open(sources_file, "w") as f:
            json.dump({"version": "1.0.0", "sources": []}, f)

        with patch("scripts.ingest.health.STATE_FILE", state_file), \
             patch("scripts.ingest.health.STAGING_DIR", tmp_staging_dir), \
             patch("scripts.ingest.health.INGEST_DIR", tmp_ingest_dir):
            results = run_health_checks()

        assert len(results) > 0
        assert all("check" in r and "severity" in r and "message" in r for r in results)
