"""Tests for dedup engine."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.ingest.dedup import DedupEngine


class TestDedupEngine:
    def test_init_default_threshold(self):
        engine = DedupEngine()
        assert engine.threshold == 0.70

    def test_init_custom_threshold(self):
        engine = DedupEngine(threshold=0.50)
        assert engine.threshold == 0.50

    def test_load_existing(self, tmp_data_dir):
        engine = DedupEngine()
        count = engine.load_existing(tmp_data_dir)
        assert count == 2

    def test_check_exact_match(self, tmp_data_dir):
        engine = DedupEngine()
        engine.load_existing(tmp_data_dir)

        score, closest = engine.check(
            "S3 bucket does not have server-side encryption enabled",
            "S3 buckets should have encryption enabled"
        )
        assert score > 0.5
        assert "encryption" in closest.lower()

    def test_check_no_match(self, tmp_data_dir):
        engine = DedupEngine()
        engine.load_existing(tmp_data_dir)

        score, closest = engine.check(
            "Lambda function timeout configuration",
            "Lambda functions should have appropriate timeout settings to prevent runaway execution costs"
        )
        assert score < 0.70

    def test_is_duplicate_true(self, tmp_data_dir):
        engine = DedupEngine(threshold=0.30)
        engine.load_existing(tmp_data_dir)

        assert engine.is_duplicate(
            "S3 bucket encryption not enabled",
            "S3 bucket default encryption is not configured"
        )

    def test_is_duplicate_false(self, tmp_data_dir):
        engine = DedupEngine()
        engine.load_existing(tmp_data_dir)

        assert not engine.is_duplicate(
            "DynamoDB table auto-scaling not configured",
            "DynamoDB tables should use auto-scaling for read and write capacity"
        )

    def test_check_empty_engine(self):
        engine = DedupEngine()
        score, closest = engine.check("anything", "something")
        assert score == 0.0
        assert closest == ""

    def test_entry_to_text(self):
        entry = {
            "scenario": "Test scenario",
            "alert_criteria": "Test criteria",
            "recommendation_action": "Test action",
            "recommendation_description_detailed": "Test description",
        }
        text = DedupEngine._entry_to_text(entry)
        assert "Test scenario" in text
        assert "Test criteria" in text
        assert "Test action" in text
