"""Deduplication engine using TF-IDF cosine similarity with optional semantic pass."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

# Optional sentence-transformers import for semantic dedup
try:
    from sentence_transformers import SentenceTransformer
    _HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    _HAS_SENTENCE_TRANSFORMERS = False

# Add project root to path for imports
_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


class DedupEngine:
    """Deduplication engine using TF-IDF cosine similarity with optional semantic pass."""

    def __init__(
        self,
        threshold: float = 0.70,
        use_semantic: bool = False,
        semantic_threshold: float = 0.75,
    ):
        self.threshold = threshold
        self.use_semantic = use_semantic
        self.semantic_threshold = semantic_threshold
        self.existing_entries: list[dict[str, Any]] = []
        self.existing_texts: list[str] = []
        self.vectorizer: TfidfVectorizer | None = None
        self.tfidf_matrix = None

        # Semantic dedup state
        self._semantic_model: Any = None
        self._semantic_embeddings: Any = None
        self._semantic_available = False

        if use_semantic and not _HAS_SENTENCE_TRANSFORMERS:
            logger.warning(
                "use_semantic=True but sentence-transformers is not installed. "
                "Falling back to TF-IDF only. Install with: pip install sentence-transformers"
            )

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

        # Load semantic model and compute embeddings if enabled and available
        if self.use_semantic and _HAS_SENTENCE_TRANSFORMERS and self.existing_texts:
            try:
                logger.info("Loading sentence-transformers model (all-MiniLM-L6-v2)...")
                self._semantic_model = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("Computing semantic embeddings for %d entries...", len(self.existing_texts))
                self._semantic_embeddings = self._semantic_model.encode(
                    self.existing_texts, show_progress_bar=False,
                )
                self._semantic_available = True
                logger.info("Semantic dedup engine ready")
            except Exception as e:
                logger.warning("Failed to initialize semantic dedup: %s. Falling back to TF-IDF only.", e)
                self._semantic_available = False

        logger.info("Loaded %d existing entries for dedup", len(self.existing_entries))
        return len(self.existing_entries)

    def check(self, title: str, body: str) -> tuple[float, str]:
        """
        Check if a new item is a duplicate of existing entries.

        Returns:
            (max_similarity_score, closest_existing_scenario)

        Uses TF-IDF cosine similarity as the primary check. If semantic mode
        is enabled and the TF-IDF score is below the threshold, a second pass
        using sentence-transformer embeddings is performed. The maximum score
        across both methods is returned.
        """
        if not self.existing_texts or self.vectorizer is None:
            return 0.0, ""

        new_text = f"{title} {body}"
        new_vector = self.vectorizer.transform([new_text])

        similarities = cosine_similarity(new_vector, self.tfidf_matrix).flatten()
        max_idx = int(similarities.argmax())
        max_score = float(similarities[max_idx])

        closest = self.existing_entries[max_idx].get("scenario", "") if max_idx < len(self.existing_entries) else ""

        # If TF-IDF already flags as duplicate, return immediately
        if max_score >= self.threshold:
            return max_score, closest

        # Second pass: semantic similarity (only if TF-IDF did NOT flag as duplicate)
        if self._semantic_available and self._semantic_model is not None and self._semantic_embeddings is not None:
            try:
                new_embedding = self._semantic_model.encode([new_text], show_progress_bar=False)
                semantic_sims = cosine_similarity(new_embedding, self._semantic_embeddings).flatten()
                semantic_max_idx = int(semantic_sims.argmax())
                semantic_max_score = float(semantic_sims[semantic_max_idx])

                # Return the higher score between TF-IDF and semantic
                if semantic_max_score > max_score:
                    max_score = semantic_max_score
                    max_idx = semantic_max_idx
                    closest = (
                        self.existing_entries[max_idx].get("scenario", "")
                        if max_idx < len(self.existing_entries)
                        else ""
                    )
                    logger.debug(
                        "Semantic dedup boosted score: %.3f -> %.3f for '%s'",
                        float(similarities.max()), semantic_max_score, title[:50],
                    )
            except Exception as e:
                logger.warning("Semantic similarity check failed: %s. Using TF-IDF score only.", e)

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
