"""Pipeline orchestrator: fetch -> filter -> dedup -> convert -> validate -> stage."""

from __future__ import annotations

import logging
import time
from typing import Any

from scripts.ingest import RawItem, INGEST_DIR, __version__
from scripts.ingest.config import load_sources, get_enabled_sources, get_fetcher, get_parser
from scripts.ingest.state import (
    load_state, save_state, is_seen, mark_seen,
    update_source_after_fetch, record_run,
)
from scripts.ingest.dedup import DedupEngine
from scripts.ingest.convert import LLMConverter
from scripts.ingest.validate_entry import validate_recommendation
from scripts.ingest.stage import stage_recommendation

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """Orchestrates the full ingestion pipeline."""

    def __init__(
        self,
        source_ids: list[str] | None = None,
        source_type: str | None = None,
        dry_run: bool = False,
        skip_llm: bool = False,
        max_items: int | None = None,
        similarity_threshold: float = 0.70,
        model: str = "claude-sonnet-4-20250514",
        verbose: bool = False,
        progress: Any = None,
    ):
        self.source_ids = source_ids
        self.source_type = source_type
        self.dry_run = dry_run
        self.skip_llm = skip_llm
        self.max_items = max_items
        self.similarity_threshold = similarity_threshold
        self.model = model
        self.verbose = verbose
        self.progress = progress

        # Pipeline components
        self.dedup = DedupEngine(threshold=similarity_threshold)
        self.converter = None if skip_llm else LLMConverter(model=model)
        self.state = load_state()

        # Metrics for this run
        self.metrics = {
            "sources_processed": 0,
            "items_fetched": 0,
            "items_filtered_seen": 0,
            "items_filtered_dedup": 0,
            "items_converted": 0,
            "items_convert_failed": 0,
            "items_convert_skipped": 0,
            "items_validated": 0,
            "items_validation_failed": 0,
            "items_staged": 0,
            "errors": [],
        }

    def run(self) -> dict[str, Any]:
        """Execute the full pipeline. Returns metrics dict."""
        start_time = time.time()

        # Load sources config
        try:
            config = load_sources()
        except (FileNotFoundError, ValueError) as e:
            logger.error("Failed to load source config: %s", e)
            self.metrics["errors"].append(str(e))
            return self.metrics

        sources = get_enabled_sources(config, self.source_type, self.source_ids)
        if not sources:
            logger.warning("No matching enabled sources found")
            return self.metrics

        # Show header
        if self.progress:
            mode = "dry-run" if self.dry_run else ("skip-llm" if self.skip_llm else "full")
            self.progress.show_header(__version__, mode, len(sources), self.similarity_threshold)

        # Load existing entries for dedup
        logger.info("Loading existing entries for deduplication...")
        num_existing = self.dedup.load_existing()
        logger.info("Loaded %d existing entries", num_existing)
        if self.progress:
            self.progress.show_dedup_loaded(num_existing)

        # Start fetch phase
        if self.progress:
            self.progress.start_fetch_phase(len(sources))

        # Process each source
        for source in sources:
            self._process_source(source)

        # End fetch phase
        if self.progress:
            self.progress.end_fetch_phase()

        # Record run
        elapsed = time.time() - start_time
        self.metrics["elapsed_seconds"] = round(elapsed, 2)
        self.metrics["sources_attempted"] = len(sources)

        if not self.dry_run:
            record_run(self.state, {
                "dry_run": False,
                "metrics": dict(self.metrics),
            })
            save_state(self.state)

        # Show summary
        if self.progress:
            self.progress.show_summary(self.metrics)
        else:
            self._print_summary()

        return self.metrics

    def _process_source(self, source: dict) -> None:
        """Process a single source through the pipeline."""
        source_id = source["id"]
        source_name = source["name"]
        source_type = source["type"]
        logger.info("Processing source: %s (%s)", source_name, source_type)

        if self.progress:
            self.progress.update_source_start(source_name, source_type)

        # Fetch
        try:
            fetcher = get_fetcher(source)
            from scripts.ingest.state import get_source_state
            source_state = get_source_state(self.state, source_id)

            result = fetcher.fetch(
                etag=source_state.get("etag"),
                last_modified=source_state.get("last_modified"),
            )

            if result["not_modified"]:
                logger.info("Source %s: not modified, skipping", source_id)
                update_source_after_fetch(self.state, source_id, result["etag"], result["last_modified"], 0)
                self.metrics["sources_processed"] += 1
                if self.progress:
                    self.progress.update_source_complete(source_name, source_type, 0, 0, not_modified=True)
                return

        except Exception as e:
            logger.error("Fetch failed for %s: %s", source_id, e)
            self.metrics["errors"].append(f"Fetch error ({source_id}): {e}")
            update_source_after_fetch(self.state, source_id, None, None, 0, error=str(e))
            if self.progress:
                self.progress.update_source_complete(source_name, source_type, 0, 0, error=str(e))
            return

        # Parse
        try:
            parser = get_parser(source)
            raw_items = parser.parse(result["content"])
        except Exception as e:
            logger.error("Parse failed for %s: %s", source_id, e)
            self.metrics["errors"].append(f"Parse error ({source_id}): {e}")
            if self.progress:
                self.progress.update_source_complete(source_name, source_type, 0, 0, error=f"Parse: {e}")
            return

        self.metrics["items_fetched"] += len(raw_items)

        # Apply max_items limit
        if self.max_items and len(raw_items) > self.max_items:
            raw_items = raw_items[:self.max_items]

        # Track per-source novel count
        seen_before = self.metrics["items_filtered_seen"]
        dedup_before = self.metrics["items_filtered_dedup"]

        # Filter and process items
        for item in raw_items:
            self._process_item(item)

        seen_delta = self.metrics["items_filtered_seen"] - seen_before
        dedup_delta = self.metrics["items_filtered_dedup"] - dedup_before
        novel_count = len(raw_items) - seen_delta - dedup_delta

        update_source_after_fetch(
            self.state, source_id, result["etag"], result["last_modified"], len(raw_items),
        )
        self.metrics["sources_processed"] += 1

        if self.progress:
            self.progress.update_source_complete(
                source_name, source_type, len(raw_items), novel_count,
            )

    def _process_item(self, item: RawItem) -> None:
        """Process a single raw item through filter -> dedup -> convert -> validate -> stage."""
        # State filter (skip seen items)
        if is_seen(self.state, item.source_id, item.content_hash):
            self.metrics["items_filtered_seen"] += 1
            if self.verbose:
                logger.debug("Skipping seen item: %s", item.title[:60])
            return

        # Mark as seen
        if not self.dry_run:
            mark_seen(self.state, item.source_id, item.content_hash)

        # Dedup check
        dedup_score, closest = self.dedup.check(item.title, item.body)
        if dedup_score >= self.similarity_threshold:
            self.metrics["items_filtered_dedup"] += 1
            if self.verbose:
                logger.info("Dedup filtered: %s (score=%.2f, closest=%s)", item.title[:40], dedup_score, closest[:40])
            return

        # Dry run stops here
        if self.dry_run:
            logger.info("[DRY RUN] Would process: %s (dedup=%.2f)", item.title[:60], dedup_score)
            return

        # LLM conversion
        if self.skip_llm:
            logger.info("[SKIP-LLM] Skipping LLM conversion: %s", item.title[:60])
            return

        if self.progress:
            self.progress.update_item_progress(item.title, "Converting")

        recommendation = self.converter.convert(item)
        if recommendation is None:
            self.metrics["items_convert_skipped"] += 1
            if self.progress:
                self.progress.advance_item()
            return

        self.metrics["items_converted"] += 1

        # Validate
        if self.progress:
            self.progress.update_item_progress(item.title, "Validating")

        is_valid, errors = validate_recommendation(recommendation)
        if not is_valid:
            self.metrics["items_validation_failed"] += 1
            logger.warning("Validation failed for %s: %s", item.title[:40], errors)

            # Retry once with errors in prompt
            if self.converter:
                logger.info("Retrying conversion with validation errors...")
                # Add errors context to body
                item_with_errors = RawItem(
                    source_id=item.source_id,
                    source_name=item.source_name,
                    title=item.title,
                    body=f"{item.body}\n\nPrevious attempt had validation errors: {errors}",
                    url=item.url,
                    published_at=item.published_at,
                    categories=item.categories,
                    raw_metadata=item.raw_metadata,
                )
                recommendation = self.converter.convert(item_with_errors)
                if recommendation is None:
                    if self.progress:
                        self.progress.advance_item()
                    return

                is_valid, errors = validate_recommendation(recommendation)
                if not is_valid:
                    logger.error("Validation still failed after retry: %s", errors)
                    if self.progress:
                        self.progress.advance_item()
                    return

        self.metrics["items_validated"] += 1

        # Stage
        if self.progress:
            self.progress.update_item_progress(item.title, "Staging")

        filepath = stage_recommendation(
            recommendation=recommendation,
            source_id=item.source_id,
            source_url=item.url,
            dedup_score=dedup_score,
            closest_existing=closest,
        )
        self.metrics["items_staged"] += 1

        if self.progress:
            self.progress.advance_item()

    def _print_summary(self):
        """Print pipeline run summary (plain text fallback)."""
        m = self.metrics
        print("\n" + "=" * 60)
        print("Pipeline Run Summary")
        print("=" * 60)
        print(f"Sources processed:  {m['sources_processed']}")
        print(f"Items fetched:      {m['items_fetched']}")
        print(f"Filtered (seen):    {m['items_filtered_seen']}")
        print(f"Filtered (dedup):   {m['items_filtered_dedup']}")
        print(f"Converted (LLM):    {m['items_converted']}")
        print(f"Convert skipped:    {m['items_convert_skipped']}")
        print(f"Validated:          {m['items_validated']}")
        print(f"Validation failed:  {m['items_validation_failed']}")
        print(f"Staged:             {m['items_staged']}")
        if m.get("elapsed_seconds"):
            print(f"Elapsed:            {m['elapsed_seconds']}s")
        if m["errors"]:
            print(f"\nErrors ({len(m['errors'])}):")
            for err in m["errors"]:
                print(f"  - {err}")
        print("=" * 60)
