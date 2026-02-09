"""Shared test fixtures for the ingest pipeline tests."""

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def tmp_data_dir(tmp_path):
    """Create a temporary data directory with by-service structure."""
    service_dir = tmp_path / "data" / "by-service"
    service_dir.mkdir(parents=True)

    # Create a sample service file
    sample_data = {
        "service": "s3",
        "count": 2,
        "misconfigurations": [
            {
                "id": "e9b21a0d-2fe8-4f5b-8875-52995b4cf2e7",
                "service_name": "s3",
                "scenario": "S3 bucket does not have server-side encryption enabled",
                "alert_criteria": "S3 bucket default encryption is not configured",
                "recommendation_action": "Enable default encryption on the S3 bucket",
                "risk_detail": "security",
                "build_priority": 0,
                "action_value": 3,
                "effort_level": 1,
                "risk_value": 3,
                "recommendation_description_detailed": "S3 buckets should have encryption enabled.",
                "category": "storage",
                "references": [],
                "metadata": {
                    "created_at": "2025-11-04T23:07:44Z",
                    "updated_at": "2025-11-04T23:07:44Z",
                    "contributors": ["initial-import"],
                    "source": "Test"
                },
                "tags": ["encryption", "s3"]
            },
            {
                "id": "03736e4a-6ce5-4375-84ce-278711247314",
                "service_name": "s3",
                "scenario": "S3 bucket has public access enabled",
                "alert_criteria": "S3 bucket allows public access",
                "recommendation_action": "Block public access",
                "risk_detail": "security",
                "build_priority": 0,
                "action_value": 3,
                "effort_level": 1,
                "risk_value": 3,
                "recommendation_description_detailed": "S3 buckets should not be publicly accessible.",
                "category": "storage",
                "references": [],
                "metadata": {
                    "created_at": "2025-11-04T23:07:44Z",
                    "updated_at": "2025-11-04T23:07:44Z",
                    "contributors": ["initial-import"],
                    "source": "Test"
                },
                "tags": ["public-access", "s3"]
            }
        ]
    }

    with open(service_dir / "s3.json", "w") as f:
        json.dump(sample_data, f, indent=2)

    return tmp_path / "data"


@pytest.fixture
def tmp_staging_dir(tmp_path):
    """Create a temporary staging directory."""
    staging = tmp_path / "staging"
    staging.mkdir(parents=True)
    return staging


@pytest.fixture
def tmp_ingest_dir(tmp_path):
    """Create a temporary ingest directory."""
    ingest = tmp_path / "ingest"
    ingest.mkdir(parents=True)
    return ingest


@pytest.fixture
def sample_source_config():
    """Sample source configuration."""
    return {
        "version": "1.0.0",
        "sources": [
            {
                "id": "test-rss-source",
                "name": "Test RSS Source",
                "type": "rss",
                "url": "https://example.com/feed.xml",
                "categories": ["security"],
                "enabled": True,
                "fetch_config": {"max_items": 10}
            },
            {
                "id": "test-html-source",
                "name": "Test HTML Source",
                "type": "html",
                "url": "https://example.com/docs",
                "categories": ["operations"],
                "enabled": True,
                "fetch_config": {},
                "parse_config": {"item_selector": ".rule-item", "title_selector": "h3"}
            },
            {
                "id": "test-github-source",
                "name": "Test GitHub Source",
                "type": "github",
                "url": "https://github.com/test/repo",
                "categories": ["security", "compliance"],
                "enabled": True,
                "fetch_config": {"branch": "main", "rules_path": "rules/", "file_pattern": "*.py"}
            },
            {
                "id": "disabled-source",
                "name": "Disabled Source",
                "type": "rss",
                "url": "https://example.com/disabled",
                "categories": ["cost"],
                "enabled": False,
                "fetch_config": {}
            }
        ]
    }


@pytest.fixture
def sample_raw_item():
    """Sample RawItem for testing."""
    from scripts.ingest import RawItem
    return RawItem(
        source_id="test-rss-source",
        source_name="Test RSS Source",
        title="Enable S3 Bucket Versioning",
        body="S3 bucket versioning should be enabled to protect against accidental deletion. "
             "Versioning allows you to preserve, retrieve, and restore every version of every object.",
        url="https://example.com/s3-versioning",
        published_at="2026-01-15T10:00:00Z",
        categories=["security"],
        raw_metadata={"author": "AWS"},
    )


@pytest.fixture
def sample_recommendation():
    """Sample recommendation dict matching the schema."""
    return {
        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "service_name": "s3",
        "scenario": "S3 bucket versioning not enabled",
        "alert_criteria": "S3 bucket does not have versioning enabled",
        "recommendation_action": "Enable versioning on the S3 bucket",
        "risk_detail": "security",
        "build_priority": 1,
        "action_value": 2,
        "effort_level": 1,
        "risk_value": 2,
        "recommendation_description_detailed": "Enable versioning to protect against accidental deletion.",
        "category": "storage",
        "references": ["https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html"],
        "metadata": {
            "created_at": "2026-02-08T12:00:00Z",
            "updated_at": "2026-02-08T12:00:00Z",
            "contributors": ["ingest-pipeline"],
            "source": "Test RSS Source"
        },
        "tags": ["versioning", "s3", "data-protection"]
    }


@pytest.fixture
def mock_schema():
    """Load the actual schema for testing."""
    schema_path = PROJECT_ROOT / "schema" / "misconfig-schema.json"
    with open(schema_path) as f:
        return json.load(f)
