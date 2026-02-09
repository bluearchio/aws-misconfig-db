"""Staging area management for candidate recommendations."""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.ingest import STAGING_DIR, DATA_DIR

logger = logging.getLogger(__name__)

_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def stage_recommendation(
    recommendation: dict,
    source_id: str,
    source_url: str,
    dedup_score: float,
    closest_existing: str,
) -> Path:
    """Write a recommendation to the staging area."""
    STAGING_DIR.mkdir(parents=True, exist_ok=True)

    rec_id = recommendation.get("id", "unknown")
    staged = {
        "staged_at": _now_iso(),
        "staged_by": "ingest-pipeline",
        "source_id": source_id,
        "source_url": source_url,
        "dedup_score": round(dedup_score, 4),
        "closest_existing": closest_existing,
        "recommendation": recommendation,
    }

    filepath = STAGING_DIR / f"{rec_id}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(staged, f, indent=2, ensure_ascii=False)
        f.write("\n")

    logger.info("Staged recommendation: %s (%s)", rec_id, recommendation.get("scenario", "")[:60])
    return filepath


def list_staged(service_filter: str | None = None) -> list[dict]:
    """List all staged recommendations."""
    if not STAGING_DIR.exists():
        return []

    staged = []
    for filepath in sorted(STAGING_DIR.glob("*.json")):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            rec = data.get("recommendation", {})
            if service_filter and rec.get("service_name") != service_filter:
                continue
            staged.append({
                "id": rec.get("id", filepath.stem),
                "file": filepath.name,
                "staged_at": data.get("staged_at", ""),
                "source_id": data.get("source_id", ""),
                "service_name": rec.get("service_name", ""),
                "scenario": rec.get("scenario", ""),
                "risk_detail": rec.get("risk_detail", ""),
                "dedup_score": data.get("dedup_score", 0),
                "closest_existing": data.get("closest_existing", ""),
            })
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("Failed to read staged file %s: %s", filepath, e)

    return staged


def promote(rec_id: str) -> tuple[bool, str]:
    """
    Promote a staged recommendation to the main database.

    Returns:
        (success, message)
    """
    staged_file = STAGING_DIR / f"{rec_id}.json"
    if not staged_file.exists():
        return False, f"Staged file not found: {rec_id}"

    with open(staged_file, "r", encoding="utf-8") as f:
        staged_data = json.load(f)

    recommendation = staged_data["recommendation"]
    service_name = recommendation.get("service_name", "").lower()

    if not service_name:
        return False, "Recommendation has no service_name"

    # Find or create service file
    service_dir = DATA_DIR / "by-service"
    service_file = service_dir / f"{service_name}.json"

    if service_file.exists():
        with open(service_file, "r", encoding="utf-8") as f:
            service_data = json.load(f)
    else:
        service_data = {
            "service": service_name,
            "count": 0,
            "misconfigurations": [],
        }

    # Check for duplicate ID
    existing_ids = {e["id"] for e in service_data["misconfigurations"]}
    if recommendation["id"] in existing_ids:
        return False, f"Duplicate ID: {recommendation['id']}"

    # Add recommendation
    service_data["misconfigurations"].append(recommendation)
    service_data["count"] = len(service_data["misconfigurations"])

    # Write service file
    with open(service_file, "w", encoding="utf-8") as f:
        json.dump(service_data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # Remove staged file
    staged_file.unlink()

    logger.info("Promoted %s to %s", rec_id, service_file)
    return True, f"Promoted to {service_file.name}"


def reject(rec_id: str, reason: str = "") -> tuple[bool, str]:
    """
    Reject a staged recommendation (removes the staged file).

    Returns:
        (success, message)
    """
    staged_file = STAGING_DIR / f"{rec_id}.json"
    if not staged_file.exists():
        return False, f"Staged file not found: {rec_id}"

    if reason:
        # Record rejection reason before removing
        with open(staged_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["rejected_at"] = _now_iso()
        data["rejection_reason"] = reason
        logger.info("Rejected %s: %s", rec_id, reason)

    staged_file.unlink()
    return True, f"Rejected: {rec_id}"
