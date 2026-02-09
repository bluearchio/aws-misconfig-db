"""Tests for staging module."""

import json
import pytest
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.ingest.stage import stage_recommendation, list_staged, promote, reject


class TestStageRecommendation:
    def test_stages_correctly(self, tmp_staging_dir, sample_recommendation):
        with patch("scripts.ingest.stage.STAGING_DIR", tmp_staging_dir):
            filepath = stage_recommendation(
                recommendation=sample_recommendation,
                source_id="test-source",
                source_url="https://example.com",
                dedup_score=0.32,
                closest_existing="Similar existing scenario",
            )

        assert filepath.exists()
        with open(filepath) as f:
            data = json.load(f)
        assert data["staged_by"] == "ingest-pipeline"
        assert data["source_id"] == "test-source"
        assert data["dedup_score"] == 0.32
        assert data["recommendation"]["service_name"] == "s3"


class TestListStaged:
    def test_empty_staging(self, tmp_staging_dir):
        with patch("scripts.ingest.stage.STAGING_DIR", tmp_staging_dir):
            result = list_staged()
        assert result == []

    def test_lists_staged_files(self, tmp_staging_dir, sample_recommendation):
        staged = {
            "staged_at": "2026-02-08T12:00:00Z",
            "staged_by": "ingest-pipeline",
            "source_id": "test",
            "source_url": "https://example.com",
            "dedup_score": 0.3,
            "closest_existing": "",
            "recommendation": sample_recommendation,
        }
        with open(tmp_staging_dir / f"{sample_recommendation['id']}.json", "w") as f:
            json.dump(staged, f)

        with patch("scripts.ingest.stage.STAGING_DIR", tmp_staging_dir):
            result = list_staged()

        assert len(result) == 1
        assert result[0]["service_name"] == "s3"

    def test_filter_by_service(self, tmp_staging_dir, sample_recommendation):
        staged = {
            "staged_at": "2026-02-08T12:00:00Z",
            "staged_by": "ingest-pipeline",
            "source_id": "test",
            "source_url": "https://example.com",
            "dedup_score": 0.3,
            "closest_existing": "",
            "recommendation": sample_recommendation,
        }
        with open(tmp_staging_dir / f"{sample_recommendation['id']}.json", "w") as f:
            json.dump(staged, f)

        with patch("scripts.ingest.stage.STAGING_DIR", tmp_staging_dir):
            result = list_staged(service_filter="ec2")
        assert len(result) == 0

        with patch("scripts.ingest.stage.STAGING_DIR", tmp_staging_dir):
            result = list_staged(service_filter="s3")
        assert len(result) == 1


class TestPromote:
    def test_promote_success(self, tmp_path, sample_recommendation):
        staging = tmp_path / "staging"
        staging.mkdir()
        data_dir = tmp_path / "data"
        service_dir = data_dir / "by-service"
        service_dir.mkdir(parents=True)

        # Create existing service file
        existing = {"service": "s3", "count": 1, "misconfigurations": [
            {"id": "existing-id", "service_name": "s3", "scenario": "existing", "risk_detail": "security"}
        ]}
        with open(service_dir / "s3.json", "w") as f:
            json.dump(existing, f)

        # Create staged file
        staged = {"staged_at": "2026-02-08T12:00:00Z", "staged_by": "test", "source_id": "test",
                  "source_url": "https://x", "dedup_score": 0.3, "closest_existing": "",
                  "recommendation": sample_recommendation}
        rec_id = sample_recommendation["id"]
        with open(staging / f"{rec_id}.json", "w") as f:
            json.dump(staged, f)

        with patch("scripts.ingest.stage.STAGING_DIR", staging), \
             patch("scripts.ingest.stage.DATA_DIR", data_dir):
            success, msg = promote(rec_id)

        assert success
        assert not (staging / f"{rec_id}.json").exists()

        with open(service_dir / "s3.json") as f:
            data = json.load(f)
        assert data["count"] == 2

    def test_promote_not_found(self, tmp_staging_dir):
        with patch("scripts.ingest.stage.STAGING_DIR", tmp_staging_dir):
            success, msg = promote("nonexistent-id")
        assert not success


class TestReject:
    def test_reject_success(self, tmp_staging_dir, sample_recommendation):
        rec_id = sample_recommendation["id"]
        staged = {"staged_at": "2026-02-08T12:00:00Z", "staged_by": "test", "source_id": "test",
                  "source_url": "https://x", "dedup_score": 0.3, "closest_existing": "",
                  "recommendation": sample_recommendation}
        with open(tmp_staging_dir / f"{rec_id}.json", "w") as f:
            json.dump(staged, f)

        with patch("scripts.ingest.stage.STAGING_DIR", tmp_staging_dir):
            success, msg = reject(rec_id, reason="Not relevant")

        assert success
        assert not (tmp_staging_dir / f"{rec_id}.json").exists()

    def test_reject_not_found(self, tmp_staging_dir):
        with patch("scripts.ingest.stage.STAGING_DIR", tmp_staging_dir):
            success, msg = reject("nonexistent")
        assert not success
