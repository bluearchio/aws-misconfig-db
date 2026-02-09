"""Source configuration loader and validator."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts.ingest import INGEST_DIR


REQUIRED_SOURCE_FIELDS = {"id", "name", "type", "url", "categories", "enabled"}
VALID_SOURCE_TYPES = {"rss", "html", "github"}


def load_sources(config_path: Path | None = None) -> dict[str, Any]:
    """Load source configuration from sources.json."""
    if config_path is None:
        config_path = INGEST_DIR / "sources.json"

    if not config_path.exists():
        raise FileNotFoundError(f"Source config not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    validate_config(config)
    return config


def validate_config(config: dict[str, Any]) -> list[str]:
    """Validate source configuration structure. Returns list of errors."""
    errors = []

    if "version" not in config:
        errors.append("Missing 'version' field")
    if "sources" not in config:
        errors.append("Missing 'sources' field")
        raise ValueError(f"Invalid source config: {'; '.join(errors)}")

    if not isinstance(config["sources"], list):
        errors.append("'sources' must be a list")
        raise ValueError(f"Invalid source config: {'; '.join(errors)}")

    seen_ids = set()
    for i, source in enumerate(config["sources"]):
        prefix = f"sources[{i}]"

        missing = REQUIRED_SOURCE_FIELDS - set(source.keys())
        if missing:
            errors.append(f"{prefix}: missing fields: {missing}")
            continue

        if source["id"] in seen_ids:
            errors.append(f"{prefix}: duplicate id '{source['id']}'")
        seen_ids.add(source["id"])

        if source["type"] not in VALID_SOURCE_TYPES:
            errors.append(f"{prefix}: invalid type '{source['type']}', must be one of {VALID_SOURCE_TYPES}")

        if not isinstance(source["categories"], list) or not source["categories"]:
            errors.append(f"{prefix}: 'categories' must be a non-empty list")

    if errors:
        raise ValueError(f"Invalid source config: {'; '.join(errors)}")

    return errors


def get_enabled_sources(config: dict[str, Any], source_type: str | None = None, source_ids: list[str] | None = None) -> list[dict]:
    """Get enabled sources, optionally filtered by type or IDs."""
    sources = [s for s in config["sources"] if s.get("enabled", True)]

    if source_type:
        sources = [s for s in sources if s["type"] == source_type]

    if source_ids:
        sources = [s for s in sources if s["id"] in source_ids]

    return sources


def get_fetcher(source: dict):
    """Get appropriate fetcher for source type."""
    from scripts.ingest.fetchers.rss import RSSFetcher
    from scripts.ingest.fetchers.html import HTMLFetcher
    from scripts.ingest.fetchers.github import GitHubFetcher

    fetchers = {
        "rss": RSSFetcher,
        "html": HTMLFetcher,
        "github": GitHubFetcher,
    }

    fetcher_cls = fetchers.get(source["type"])
    if not fetcher_cls:
        raise ValueError(f"No fetcher for source type: {source['type']}")

    return fetcher_cls(source)


def get_parser(source: dict):
    """Get appropriate parser for source type."""
    from scripts.ingest.parsers.rss_parser import RSSParser
    from scripts.ingest.parsers.html_parser import HTMLParser
    from scripts.ingest.parsers.github_parser import GitHubParser

    parsers = {
        "rss": RSSParser,
        "html": HTMLParser,
        "github": GitHubParser,
    }

    parser_cls = parsers.get(source["type"])
    if not parser_cls:
        raise ValueError(f"No parser for source type: {source['type']}")

    return parser_cls(source)
