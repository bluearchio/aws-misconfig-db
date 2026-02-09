"""Pipeline state management."""

from __future__ import annotations

import json
import logging
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.ingest import INGEST_DIR

logger = logging.getLogger(__name__)

STATE_FILE = INGEST_DIR / "state.json"
MAX_HASHES_PER_SOURCE = 10000
MAX_RUNS = 100


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_state(state_path: Path | None = None) -> dict[str, Any]:
    """Load pipeline state. Returns default state if file doesn't exist."""
    if state_path is None:
        state_path = STATE_FILE

    if not state_path.exists():
        return _default_state()

    try:
        with open(state_path, "r", encoding="utf-8") as f:
            state = json.load(f)

        # Validate basic structure
        if not isinstance(state, dict) or "sources" not in state:
            raise ValueError("Invalid state structure")

        return state

    except (json.JSONDecodeError, ValueError) as e:
        logger.critical("State file corrupted: %s", e)
        # Backup corrupt file
        backup = state_path.with_suffix(f".corrupt.{datetime.now().strftime('%Y%m%d%H%M%S')}")
        shutil.copy2(state_path, backup)
        logger.critical("Backed up corrupt state to %s", backup)
        return _default_state()


def save_state(state: dict[str, Any], state_path: Path | None = None) -> None:
    """Save state atomically via tmp file + rename."""
    if state_path is None:
        state_path = STATE_FILE

    state_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = state_path.with_suffix(".tmp")

    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
        f.write("\n")

    os.replace(tmp_path, state_path)


def _default_state() -> dict[str, Any]:
    return {
        "version": "1.0.0",
        "sources": {},
        "runs": [],
    }


def get_source_state(state: dict, source_id: str) -> dict:
    """Get state for a specific source, creating default if needed."""
    if source_id not in state["sources"]:
        state["sources"][source_id] = {
            "last_fetched_at": None,
            "etag": None,
            "last_modified": None,
            "content_hashes": {},
            "consecutive_empty": 0,
            "consecutive_errors": 0,
        }
    return state["sources"][source_id]


def is_seen(state: dict, source_id: str, content_hash: str) -> bool:
    """Check if content hash has been seen for this source."""
    source_state = get_source_state(state, source_id)
    return content_hash in source_state["content_hashes"]


def mark_seen(state: dict, source_id: str, content_hash: str) -> None:
    """Mark content hash as seen for this source."""
    source_state = get_source_state(state, source_id)
    hashes = source_state["content_hashes"]
    hashes[content_hash] = _now_iso()

    # Prune oldest if over limit
    if len(hashes) > MAX_HASHES_PER_SOURCE:
        sorted_items = sorted(hashes.items(), key=lambda x: x[1])
        excess = len(hashes) - MAX_HASHES_PER_SOURCE
        for key, _ in sorted_items[:excess]:
            del hashes[key]


def record_run(state: dict, run_data: dict) -> None:
    """Record a pipeline run with metrics."""
    run_data["timestamp"] = _now_iso()
    state["runs"].append(run_data)

    # Cap runs list
    if len(state["runs"]) > MAX_RUNS:
        state["runs"] = state["runs"][-MAX_RUNS:]


def update_source_after_fetch(state: dict, source_id: str, etag: str | None, last_modified: str | None, items_count: int, error: str | None = None) -> None:
    """Update source state after a fetch attempt."""
    source_state = get_source_state(state, source_id)
    source_state["last_fetched_at"] = _now_iso()

    if etag:
        source_state["etag"] = etag
    if last_modified:
        source_state["last_modified"] = last_modified

    if error:
        source_state["consecutive_errors"] = source_state.get("consecutive_errors", 0) + 1
    else:
        source_state["consecutive_errors"] = 0

    if items_count == 0 and not error:
        source_state["consecutive_empty"] = source_state.get("consecutive_empty", 0) + 1
    else:
        source_state["consecutive_empty"] = 0
