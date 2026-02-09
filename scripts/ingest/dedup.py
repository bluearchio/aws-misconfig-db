"""Deduplication engine using TF-IDF cosine similarity."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

# Add project root to path for imports
_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


class DedupEngine:
    """Deduplication engine using TF-IDF cosine similarity."""

    def __init__(self, threshold: float = 0.70):
        self.threshold = threshold
        self.existing_entries: list[dict[str, Any]] = []
        self.existing_texts: list[str] = []
        self.vectorizer: TfidfVectorizer | None = None
        self.tfidf_matrix = None

    def load_existing(self, data_dir: Path | None = None) -> int:
        """Load existing recommendations for comparison."""
        if data_dir is None:
            data_dir = _project_root / "data"

        # Import from existing generate.py
        from scripts.generate import load_all_entries

        self.existing_entries = load_all_entries(data_dir)

        # Build text representations for comparison
        self.existing_texts = []
        for entry in self.existing_entries:
            text = self._entry_to_text(entry)
            self.existing_texts.append(text)

        if self.existing_texts:
            self.vectorizer = TfidfVectorizer(
                stop_words="english",
                max_features=5000,
                ngram_range=(1, 2),
            )
            self.tfidf_matrix = self.vectorizer.fit_transform(self.existing_texts)

        logger.info("Loaded %d existing entries for dedup", len(self.existing_entries))
        return len(self.existing_entries)

    def check(self, title: str, body: str) -> tuple[float, str]:
        """
        Check if a new item is a duplicate of existing entries.

        Returns:
            (max_similarity_score, closest_existing_scenario)
        """
        if not self.existing_texts or self.vectorizer is None:
            return 0.0, ""

        new_text = f"{title} {body}"
        new_vector = self.vectorizer.transform([new_text])

        similarities = cosine_similarity(new_vector, self.tfidf_matrix).flatten()
        max_idx = similarities.argmax()
        max_score = float(similarities[max_idx])

        closest = self.existing_entries[max_idx].get("scenario", "") if max_idx < len(self.existing_entries) else ""

        return max_score, closest

    def is_duplicate(self, title: str, body: str) -> bool:
        """Check if item exceeds similarity threshold."""
        score, _ = self.check(title, body)
        return score >= self.threshold

    @staticmethod
    def _entry_to_text(entry: dict) -> str:
        """Convert an existing entry to comparable text."""
        parts = [
            entry.get("scenario", ""),
            entry.get("alert_criteria", ""),
            entry.get("recommendation_action", ""),
            entry.get("recommendation_description_detailed", ""),
        ]
        return " ".join(p for p in parts if p)
