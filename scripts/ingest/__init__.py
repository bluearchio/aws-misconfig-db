"""AWS Misconfiguration Ingest Pipeline."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

__version__ = "1.0.0"

BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"
INGEST_DIR = DATA_DIR / "ingest"
STAGING_DIR = DATA_DIR / "staging"
SCHEMA_DIR = BASE_DIR / "schema"


@dataclass
class RawItem:
    """A raw item extracted from a source, before conversion to recommendation format."""
    source_id: str           # e.g., "aws-security-blog"
    source_name: str         # e.g., "AWS Security Blog"
    title: str
    body: str                # Full text content
    url: str
    published_at: str | None = None  # ISO 8601 if available
    content_hash: str = ""   # SHA-256 of normalized title+body
    categories: list[str] = field(default_factory=list)
    raw_metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.content_hash:
            self.content_hash = self.compute_hash()

    def compute_hash(self) -> str:
        """Compute SHA-256 hash of normalized title + body."""
        normalized = f"{self.title.strip().lower()}|{self.body.strip().lower()}"
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
