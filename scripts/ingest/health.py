"""Health check definitions and reporter."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from scripts.ingest import INGEST_DIR, STAGING_DIR

logger = logging.getLogger(__name__)

STATE_FILE = INGEST_DIR / "state.json"

STALE_THRESHOLD_DAYS = 7
STAGING_OVERFLOW_LIMIT = 100
CONSECUTIVE_EMPTY_THRESHOLD = 3
CONSECUTIVE_ERROR_THRESHOLD = 3


def check_source_yields(state: dict, config: dict) -> list[dict]:
    """Check for sources that yield zero items consistently."""
    results = []
    for source_id, src_state in state.get("sources", {}).items():
        empty_count = src_state.get("consecutive_empty", 0)
        if empty_count >= CONSECUTIVE_EMPTY_THRESHOLD:
            results.append({
                "check": "source_yields_zero",
                "severity": "WARNING",
                "message": f"Source '{source_id}' has returned 0 items for {empty_count} consecutive runs",
            })
        else:
            results.append({
                "check": "source_yields_zero",
                "severity": "OK",
                "message": f"Source '{source_id}': consecutive empty = {empty_count}",
            })
    return results


def check_http_errors(state: dict, config: dict) -> list[dict]:
    """Check for persistent HTTP errors."""
    results = []
    for source_id, src_state in state.get("sources", {}).items():
        err_count = src_state.get("consecutive_errors", 0)
        if err_count >= CONSECUTIVE_ERROR_THRESHOLD:
            results.append({
                "check": "http_errors",
                "severity": "ERROR",
                "message": f"Source '{source_id}' has had {err_count} consecutive fetch errors",
            })
        else:
            results.append({
                "check": "http_errors",
                "severity": "OK",
                "message": f"Source '{source_id}': consecutive errors = {err_count}",
            })
    return results


def check_stale_sources(state: dict, config: dict) -> list[dict]:
    """Check for enabled sources not fetched recently."""
    results = []
    now = datetime.now(timezone.utc)
    threshold = now - timedelta(days=STALE_THRESHOLD_DAYS)

    for source in config.get("sources", []):
        if not source.get("enabled", True):
            continue

        source_id = source["id"]
        src_state = state.get("sources", {}).get(source_id, {})
        last_fetched = src_state.get("last_fetched_at")

        if not last_fetched:
            results.append({
                "check": "stale_source",
                "severity": "WARNING",
                "message": f"Source '{source_id}' has never been fetched",
            })
        else:
            try:
                fetched_dt = datetime.fromisoformat(last_fetched.replace("Z", "+00:00"))
                if fetched_dt < threshold:
                    days_ago = (now - fetched_dt).days
                    results.append({
                        "check": "stale_source",
                        "severity": "WARNING",
                        "message": f"Source '{source_id}' last fetched {days_ago} days ago",
                    })
                else:
                    results.append({
                        "check": "stale_source",
                        "severity": "OK",
                        "message": f"Source '{source_id}' fetched recently",
                    })
            except (ValueError, TypeError):
                results.append({
                    "check": "stale_source",
                    "severity": "WARNING",
                    "message": f"Source '{source_id}' has invalid last_fetched_at",
                })

    return results


def check_staging_overflow() -> list[dict]:
    """Check if staging area has too many unreviewed items."""
    if not STAGING_DIR.exists():
        return [{"check": "staging_overflow", "severity": "OK", "message": "No staging directory"}]

    count = len(list(STAGING_DIR.glob("*.json")))
    if count >= STAGING_OVERFLOW_LIMIT:
        return [{
            "check": "staging_overflow",
            "severity": "WARNING",
            "message": f"Staging has {count} unreviewed items (threshold: {STAGING_OVERFLOW_LIMIT})",
        }]
    return [{"check": "staging_overflow", "severity": "OK", "message": f"Staging has {count} items"}]


def check_state_corruption() -> list[dict]:
    """Check if state file is valid."""
    if not STATE_FILE.exists():
        return [{"check": "state_corruption", "severity": "OK", "message": "No state file (will be created on first run)"}]

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
        if not isinstance(state, dict) or "sources" not in state:
            return [{"check": "state_corruption", "severity": "CRITICAL", "message": "State file has invalid structure"}]
        return [{"check": "state_corruption", "severity": "OK", "message": "State file is valid"}]
    except json.JSONDecodeError as e:
        return [{"check": "state_corruption", "severity": "CRITICAL", "message": f"State file is not valid JSON: {e}"}]
    except Exception as e:
        return [{"check": "state_corruption", "severity": "CRITICAL", "message": f"Cannot read state file: {e}"}]


def check_run_quality(state: dict) -> list[dict]:
    """Check recent run quality metrics."""
    results = []
    runs = state.get("runs", [])

    if not runs:
        return [{"check": "run_quality", "severity": "OK", "message": "No runs recorded yet"}]

    last_run = runs[-1]
    metrics = last_run.get("metrics", {})

    # Check conversion rate
    converted = metrics.get("items_converted", 0)
    convert_failed = metrics.get("items_convert_failed", 0)
    total_convert = converted + convert_failed
    if total_convert > 0:
        rate = converted / total_convert
        if rate < 0.50:
            results.append({
                "check": "low_conversion_rate",
                "severity": "WARNING",
                "message": f"LLM conversion rate was {rate:.0%} in last run ({converted}/{total_convert})",
            })

    # Check validation failures
    validated = metrics.get("items_validated", 0)
    val_failed = metrics.get("items_validation_failed", 0)
    total_val = validated + val_failed
    if total_val > 0 and val_failed / total_val > 0.10:
        results.append({
            "check": "schema_failures",
            "severity": "ERROR",
            "message": f"Schema validation failure rate {val_failed/total_val:.0%} in last run",
        })

    if not results:
        results.append({"check": "run_quality", "severity": "OK", "message": "Last run quality is acceptable"})

    return results


def run_health_checks(checks: list[str] | None = None) -> list[dict]:
    """Run all or specified health checks."""
    results = []

    # Load state
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        state = {"sources": {}, "runs": []}

    # Load config
    try:
        config_file = INGEST_DIR / "sources.json"
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        config = {"sources": []}

    all_checks = {
        "sources": lambda: check_source_yields(state, config),
        "state": lambda: check_state_corruption(),
        "staging": lambda: check_staging_overflow(),
        "stale": lambda: check_stale_sources(state, config),
        "errors": lambda: check_http_errors(state, config),
        "quality": lambda: check_run_quality(state),
    }

    checks_to_run = checks or list(all_checks.keys())

    for check_name in checks_to_run:
        if check_name in all_checks:
            try:
                results.extend(all_checks[check_name]())
            except Exception as e:
                results.append({
                    "check": check_name,
                    "severity": "ERROR",
                    "message": f"Health check failed: {e}",
                })

    return results
