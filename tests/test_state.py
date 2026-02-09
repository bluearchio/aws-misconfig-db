"""Tests for state management."""

import json
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.ingest.state import (
    load_state, save_state, get_source_state, is_seen, mark_seen,
    record_run, update_source_after_fetch, MAX_HASHES_PER_SOURCE, MAX_RUNS,
)


class TestLoadState:
    def test_returns_default_when_no_file(self, tmp_path):
        state = load_state(tmp_path / "nonexistent.json")
        assert state["version"] == "1.0.0"
        assert state["sources"] == {}
        assert state["runs"] == []

    def test_loads_existing_file(self, tmp_path):
        state_file = tmp_path / "state.json"
        state_data = {"version": "1.0.0", "sources": {"test": {}}, "runs": []}
        with open(state_file, "w") as f:
            json.dump(state_data, f)

        state = load_state(state_file)
        assert "test" in state["sources"]

    def test_handles_corrupt_file(self, tmp_path):
        state_file = tmp_path / "state.json"
        state_file.write_text("not json{{{")

        state = load_state(state_file)
        assert state["version"] == "1.0.0"
        # Should have created backup
        backups = list(tmp_path.glob("state.corrupt.*"))
        assert len(backups) == 1


class TestSaveState:
    def test_save_and_reload(self, tmp_path):
        state_file = tmp_path / "state.json"
        state = {"version": "1.0.0", "sources": {"test": {"last_fetched_at": "2026-01-01T00:00:00Z"}}, "runs": []}

        save_state(state, state_file)

        loaded = load_state(state_file)
        assert loaded["sources"]["test"]["last_fetched_at"] == "2026-01-01T00:00:00Z"

    def test_creates_parent_dirs(self, tmp_path):
        state_file = tmp_path / "sub" / "dir" / "state.json"
        save_state({"version": "1.0.0", "sources": {}, "runs": []}, state_file)
        assert state_file.exists()


class TestSourceState:
    def test_get_creates_default(self):
        state = {"version": "1.0.0", "sources": {}, "runs": []}
        source_state = get_source_state(state, "new-source")
        assert source_state["last_fetched_at"] is None
        assert source_state["content_hashes"] == {}
        assert source_state["consecutive_empty"] == 0

    def test_is_seen_false(self):
        state = {"version": "1.0.0", "sources": {}, "runs": []}
        assert not is_seen(state, "src", "hash123")

    def test_mark_and_check_seen(self):
        state = {"version": "1.0.0", "sources": {}, "runs": []}
        mark_seen(state, "src", "hash123")
        assert is_seen(state, "src", "hash123")

    def test_hash_pruning(self):
        state = {"version": "1.0.0", "sources": {}, "runs": []}
        for i in range(MAX_HASHES_PER_SOURCE + 100):
            mark_seen(state, "src", f"hash-{i:06d}")

        source_state = get_source_state(state, "src")
        assert len(source_state["content_hashes"]) <= MAX_HASHES_PER_SOURCE


class TestRecordRun:
    def test_appends_run(self):
        state = {"version": "1.0.0", "sources": {}, "runs": []}
        record_run(state, {"items_fetched": 10})
        assert len(state["runs"]) == 1
        assert "timestamp" in state["runs"][0]

    def test_caps_at_max(self):
        state = {"version": "1.0.0", "sources": {}, "runs": []}
        for i in range(MAX_RUNS + 10):
            record_run(state, {"run": i})
        assert len(state["runs"]) == MAX_RUNS


class TestUpdateSourceAfterFetch:
    def test_updates_on_success(self):
        state = {"version": "1.0.0", "sources": {}, "runs": []}
        update_source_after_fetch(state, "src", "etag-1", "mod-1", 5)

        src = state["sources"]["src"]
        assert src["etag"] == "etag-1"
        assert src["last_modified"] == "mod-1"
        assert src["consecutive_errors"] == 0

    def test_increments_errors(self):
        state = {"version": "1.0.0", "sources": {}, "runs": []}
        update_source_after_fetch(state, "src", None, None, 0, error="timeout")
        assert state["sources"]["src"]["consecutive_errors"] == 1

        update_source_after_fetch(state, "src", None, None, 0, error="timeout again")
        assert state["sources"]["src"]["consecutive_errors"] == 2

    def test_resets_errors_on_success(self):
        state = {"version": "1.0.0", "sources": {}, "runs": []}
        update_source_after_fetch(state, "src", None, None, 0, error="err")
        update_source_after_fetch(state, "src", None, None, 5)
        assert state["sources"]["src"]["consecutive_errors"] == 0

    def test_tracks_consecutive_empty(self):
        state = {"version": "1.0.0", "sources": {}, "runs": []}
        update_source_after_fetch(state, "src", None, None, 0)
        update_source_after_fetch(state, "src", None, None, 0)
        assert state["sources"]["src"]["consecutive_empty"] == 2

        update_source_after_fetch(state, "src", None, None, 3)
        assert state["sources"]["src"]["consecutive_empty"] == 0
