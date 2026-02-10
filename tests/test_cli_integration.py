"""Integration tests for scripts/ingest/cli.py subcommands."""

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from argparse import Namespace

import pytest

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.ingest.cli import (
    cmd_list_sources,
    cmd_show_staged,
    cmd_promote,
    cmd_reject,
)


def _write_sources_config(path, config):
    """Helper: write a sources.json config file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2))


class TestCmdListSources:
    def test_list_all(self, tmp_path, sample_source_config, capsys):
        """list-sources should list all configured sources."""
        config_path = tmp_path / "sources.json"
        _write_sources_config(config_path, sample_source_config)

        args = Namespace(enabled_only=False, format="table")
        with patch("scripts.ingest.cli.load_sources", return_value=sample_source_config):
            result = cmd_list_sources(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "test-rss-source" in captured.out
        assert "test-html-source" in captured.out
        assert "disabled-source" in captured.out

    def test_list_enabled_only(self, tmp_path, sample_source_config, capsys):
        """list-sources --enabled-only should exclude disabled sources."""
        args = Namespace(enabled_only=True, format="table")
        with patch("scripts.ingest.cli.load_sources", return_value=sample_source_config):
            result = cmd_list_sources(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "test-rss-source" in captured.out
        # disabled-source should NOT be in output
        assert "disabled-source" not in captured.out

    def test_json_format(self, tmp_path, sample_source_config, capsys):
        """list-sources --format json should output valid JSON."""
        args = Namespace(enabled_only=False, format="json")
        with patch("scripts.ingest.cli.load_sources", return_value=sample_source_config):
            result = cmd_list_sources(args)

        assert result == 0
        captured = capsys.readouterr()
        # The first output should be parseable as JSON
        data = json.loads(captured.out.strip())
        assert isinstance(data, list)
        assert len(data) == 4

    def test_load_error(self, capsys):
        """list-sources should handle missing config gracefully."""
        args = Namespace(enabled_only=False, format="table")
        with patch("scripts.ingest.cli.load_sources", side_effect=FileNotFoundError("not found")):
            result = cmd_list_sources(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Error" in captured.err or "not found" in captured.err


class TestCmdShowStaged:
    def test_empty_staging(self, capsys):
        """show-staged should report no staged recommendations when staging is empty."""
        args = Namespace(format="table", filter_service=None)
        with patch("scripts.ingest.cli.list_staged", return_value=[]):
            result = cmd_show_staged(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "No staged" in captured.out

    def test_with_staged_items(self, capsys, sample_recommendation):
        """show-staged should display staged recommendations."""
        staged_items = [
            {
                "id": sample_recommendation["id"],
                "file": f"{sample_recommendation['id']}.json",
                "staged_at": "2026-02-08T12:00:00Z",
                "source_id": "test-source",
                "service_name": "s3",
                "scenario": "S3 bucket versioning not enabled",
                "risk_detail": "security",
                "dedup_score": 0.32,
                "closest_existing": "Similar existing scenario text",
            }
        ]
        args = Namespace(format="table", filter_service=None)
        with patch("scripts.ingest.cli.list_staged", return_value=staged_items):
            result = cmd_show_staged(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "s3" in captured.out.lower() or "S3" in captured.out

    def test_json_format(self, capsys, sample_recommendation):
        """show-staged --format json should output valid JSON."""
        staged_items = [
            {
                "id": sample_recommendation["id"],
                "file": f"{sample_recommendation['id']}.json",
                "staged_at": "2026-02-08T12:00:00Z",
                "source_id": "test-source",
                "service_name": "s3",
                "scenario": "S3 bucket versioning not enabled",
                "risk_detail": "security",
                "dedup_score": 0.32,
                "closest_existing": "Similar existing scenario text",
            }
        ]
        args = Namespace(format="json", filter_service=None)
        with patch("scripts.ingest.cli.list_staged", return_value=staged_items):
            result = cmd_show_staged(args)

        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out.strip())
        assert isinstance(data, list)
        assert len(data) == 1

    def test_detail_format(self, capsys, sample_recommendation):
        """show-staged --format detail should display full item details."""
        staged_items = [
            {
                "id": sample_recommendation["id"],
                "file": f"{sample_recommendation['id']}.json",
                "staged_at": "2026-02-08T12:00:00Z",
                "source_id": "test-source",
                "service_name": "s3",
                "scenario": "S3 bucket versioning not enabled",
                "risk_detail": "security",
                "dedup_score": 0.32,
                "closest_existing": "Similar existing scenario text",
            }
        ]
        args = Namespace(format="detail", filter_service=None)
        with patch("scripts.ingest.cli.list_staged", return_value=staged_items):
            result = cmd_show_staged(args)

        assert result == 0
        captured = capsys.readouterr()
        assert sample_recommendation["id"] in captured.out


class TestCmdPromote:
    def test_promote_success(self, capsys):
        """promote should report success when promote() returns True."""
        args = Namespace(uuid="test-uuid-1234")
        with patch("scripts.ingest.cli.promote", return_value=(True, "Promoted to s3.json")):
            result = cmd_promote(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Promoted" in captured.out

    def test_promote_not_found(self, capsys):
        """promote should report failure when the staged file is not found."""
        args = Namespace(uuid="nonexistent-uuid")
        with patch("scripts.ingest.cli.promote", return_value=(False, "Staged file not found: nonexistent-uuid")):
            result = cmd_promote(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.out

    def test_promote_duplicate(self, capsys):
        """promote should report failure on duplicate ID."""
        args = Namespace(uuid="dup-uuid")
        with patch("scripts.ingest.cli.promote", return_value=(False, "Duplicate ID: dup-uuid")):
            result = cmd_promote(args)

        assert result == 1


class TestCmdReject:
    def test_reject_success(self, capsys):
        """reject should report success when reject() returns True."""
        args = Namespace(uuid="test-uuid-1234", reason="Not relevant")
        with patch("scripts.ingest.cli.reject", return_value=(True, "Rejected: test-uuid-1234")):
            result = cmd_reject(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Rejected" in captured.out

    def test_reject_with_reason(self, capsys):
        """reject with a reason should pass the reason through."""
        args = Namespace(uuid="test-uuid-5678", reason="Duplicate of existing")
        with patch("scripts.ingest.cli.reject", return_value=(True, "Rejected: test-uuid-5678")) as mock_reject:
            result = cmd_reject(args)

        assert result == 0
        # Verify reject was called with the reason
        mock_reject.assert_called_once_with("test-uuid-5678", reason="Duplicate of existing")

    def test_reject_not_found(self, capsys):
        """reject should report failure when the staged file is not found."""
        args = Namespace(uuid="nonexistent-uuid", reason="")
        with patch("scripts.ingest.cli.reject", return_value=(False, "Staged file not found: nonexistent-uuid")):
            result = cmd_reject(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.out

    def test_reject_no_reason(self, capsys):
        """reject without a reason should default to empty string."""
        args = Namespace(uuid="test-uuid-9999", reason=None)
        with patch("scripts.ingest.cli.reject", return_value=(True, "Rejected: test-uuid-9999")) as mock_reject:
            result = cmd_reject(args)

        assert result == 0
        mock_reject.assert_called_once_with("test-uuid-9999", reason="")
