"""Validation wrapper for recommendation entries."""

from __future__ import annotations

import sys
from pathlib import Path

_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from scripts.validate import load_schema, validate_entry

SCHEMA_PATH = _project_root / "schema" / "misconfig-schema.json"

_schema_cache: dict | None = None


def get_schema() -> dict:
    """Load and cache the schema."""
    global _schema_cache
    if _schema_cache is None:
        _schema_cache = load_schema(SCHEMA_PATH)
    return _schema_cache


def validate_recommendation(entry: dict) -> tuple[bool, list[str]]:
    """Validate a recommendation entry against the schema."""
    schema = get_schema()
    return validate_entry(entry, schema)
