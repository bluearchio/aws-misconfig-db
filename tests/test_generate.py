"""Tests for scripts/generate.py — stats generation and markdown output."""

import json
import sys
from pathlib import Path

import pytest

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.generate import load_all_entries, generate_stats, generate_markdown_summary


class TestLoadAllEntries:
    def test_loads_entries(self, tmp_data_dir):
        """Should find 2 entries from s3.json in tmp_data_dir."""
        entries = load_all_entries(tmp_data_dir)
        assert len(entries) == 2
        assert entries[0]["service_name"] == "s3"
        assert entries[1]["service_name"] == "s3"

    def test_empty_dir(self, tmp_path):
        """Empty by-service directory should return no entries."""
        service_dir = tmp_path / "by-service"
        service_dir.mkdir(parents=True)
        entries = load_all_entries(tmp_path)
        assert entries == []

    def test_missing_dir(self, tmp_path):
        """Missing by-service directory should return no entries."""
        entries = load_all_entries(tmp_path)
        assert entries == []

    def test_multiple_service_files(self, tmp_path):
        """Entries from multiple service files should be combined."""
        service_dir = tmp_path / "by-service"
        service_dir.mkdir(parents=True)

        s3_data = {
            "service": "s3",
            "count": 1,
            "misconfigurations": [
                {"id": "id-1", "service_name": "s3", "scenario": "S3 test", "risk_detail": "security"},
            ],
        }
        ec2_data = {
            "service": "ec2",
            "count": 1,
            "misconfigurations": [
                {"id": "id-2", "service_name": "ec2", "scenario": "EC2 test", "risk_detail": "cost"},
            ],
        }
        (service_dir / "s3.json").write_text(json.dumps(s3_data))
        (service_dir / "ec2.json").write_text(json.dumps(ec2_data))

        entries = load_all_entries(tmp_path)
        assert len(entries) == 2
        service_names = {e["service_name"] for e in entries}
        assert service_names == {"s3", "ec2"}

    def test_ignores_non_misconfig_keys(self, tmp_path):
        """Files without 'misconfigurations' key should be skipped."""
        service_dir = tmp_path / "by-service"
        service_dir.mkdir(parents=True)

        data = {"not_misconfigurations": [{"id": "x"}]}
        (service_dir / "bad.json").write_text(json.dumps(data))

        entries = load_all_entries(tmp_path)
        assert entries == []


class TestGenerateStats:
    def test_basic_stats(self, tmp_data_dir):
        """Stats should contain correct total and service breakdown."""
        entries = load_all_entries(tmp_data_dir)
        stats = generate_stats(entries)

        assert stats["total_entries"] == 2
        assert stats["by_service"]["s3"] == 2
        assert len(stats["by_service"]) == 1

    def test_risk_type_counts(self):
        """Test risk type counting with multiple risk types."""
        entries = [
            {"service_name": "s3", "risk_detail": "security", "category": "storage"},
            {"service_name": "ec2", "risk_detail": "cost", "category": "compute"},
            {"service_name": "rds", "risk_detail": "security, cost", "category": "database"},
        ]
        stats = generate_stats(entries)

        assert stats["by_risk_type"]["security"] == 2
        assert stats["by_risk_type"]["cost"] == 2

    def test_category_counts(self):
        """Test category counting."""
        entries = [
            {"service_name": "s3", "risk_detail": "security", "category": "storage"},
            {"service_name": "ebs", "risk_detail": "cost", "category": "storage"},
            {"service_name": "ec2", "risk_detail": "security", "category": "compute"},
        ]
        stats = generate_stats(entries)

        assert stats["by_category"]["storage"] == 2
        assert stats["by_category"]["compute"] == 1

    def test_priority_counts(self):
        """Test build priority counting."""
        entries = [
            {"service_name": "s3", "risk_detail": "security", "build_priority": 0},
            {"service_name": "ec2", "risk_detail": "cost", "build_priority": 1},
            {"service_name": "rds", "risk_detail": "security", "build_priority": 0},
        ]
        stats = generate_stats(entries)

        assert stats["by_priority"]["0"] == 2
        assert stats["by_priority"]["1"] == 1

    def test_empty_entries(self):
        """Stats for empty entries list should have zero totals."""
        stats = generate_stats([])
        assert stats["total_entries"] == 0
        assert stats["by_service"] == {}

    def test_missing_optional_fields(self):
        """Entries missing optional fields should not cause errors."""
        entries = [
            {"service_name": "s3", "risk_detail": "security"},
        ]
        stats = generate_stats(entries)
        assert stats["total_entries"] == 1
        assert stats["by_category"] == {}
        assert stats["by_priority"] == {}


class TestGenerateMarkdownSummary:
    def _make_stats(self):
        """Create sample stats dict for markdown generation."""
        return {
            "total_entries": 10,
            "by_service": {"s3": 5, "ec2": 3, "rds": 2},
            "by_category": {"storage": 5, "compute": 3, "database": 2},
            "by_risk_type": {"security": 7, "cost": 3},
            "by_priority": {"0": 4, "1": 3, "2": 2, "3": 1},
        }

    def test_creates_file(self, tmp_path):
        """Markdown file should be created at the specified path."""
        stats = self._make_stats()
        output = tmp_path / "docs" / "SUMMARY.md"
        generate_markdown_summary(stats, output)
        assert output.exists()

    def test_contains_total(self, tmp_path):
        """Markdown should contain the total recommendation count."""
        stats = self._make_stats()
        output = tmp_path / "SUMMARY.md"
        generate_markdown_summary(stats, output)
        content = output.read_text()
        assert "10" in content
        assert "Total Recommendations" in content

    def test_contains_risk_table(self, tmp_path):
        """Markdown should contain the risk type table."""
        stats = self._make_stats()
        output = tmp_path / "SUMMARY.md"
        generate_markdown_summary(stats, output)
        content = output.read_text()
        assert "Risk Type" in content
        assert "security" in content
        assert "cost" in content

    def test_contains_service_table(self, tmp_path):
        """Markdown should contain the service table."""
        stats = self._make_stats()
        output = tmp_path / "SUMMARY.md"
        generate_markdown_summary(stats, output)
        content = output.read_text()
        assert "By Service" in content
        assert "s3" in content
        assert "ec2" in content

    def test_contains_category_table(self, tmp_path):
        """Markdown should contain the category table."""
        stats = self._make_stats()
        output = tmp_path / "SUMMARY.md"
        generate_markdown_summary(stats, output)
        content = output.read_text()
        assert "By Category" in content
        assert "storage" in content

    def test_contains_priority_table(self, tmp_path):
        """Markdown should contain the priority table."""
        stats = self._make_stats()
        output = tmp_path / "SUMMARY.md"
        generate_markdown_summary(stats, output)
        content = output.read_text()
        assert "By Priority" in content

    def test_creates_parent_dirs(self, tmp_path):
        """Should create parent directories if they don't exist."""
        stats = self._make_stats()
        output = tmp_path / "nested" / "dir" / "SUMMARY.md"
        generate_markdown_summary(stats, output)
        assert output.exists()

    def test_empty_categories_no_table(self, tmp_path):
        """If by_category is empty, the category table should not appear."""
        stats = self._make_stats()
        stats["by_category"] = {}
        output = tmp_path / "SUMMARY.md"
        generate_markdown_summary(stats, output)
        content = output.read_text()
        assert "By Category" not in content

    def test_empty_priorities_no_table(self, tmp_path):
        """If by_priority is empty, the priority table should not appear."""
        stats = self._make_stats()
        stats["by_priority"] = {}
        output = tmp_path / "SUMMARY.md"
        generate_markdown_summary(stats, output)
        content = output.read_text()
        assert "By Priority" not in content
