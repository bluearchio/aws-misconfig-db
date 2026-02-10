"""Tests for scripts/db-init.py and scripts/db-query.py — DuckDB database operations."""

import importlib
import json
import sys
from pathlib import Path
from unittest.mock import patch

import duckdb
import pytest

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import hyphenated modules using importlib
db_init = importlib.import_module("scripts.db-init")
db_query = importlib.import_module("scripts.db-query")


class TestFlattenEntry:
    def test_basic_flatten(self, sample_recommendation):
        """Flattened entry should have top-level keys for nested fields."""
        flat = db_init.flatten_entry(sample_recommendation)

        assert flat["id"] == sample_recommendation["id"]
        assert flat["service_name"] == "s3"
        assert flat["scenario"] == sample_recommendation["scenario"]
        assert flat["build_priority"] == 1
        assert flat["category"] == "storage"

    def test_flattens_metadata(self, sample_recommendation):
        """Metadata fields should be flattened to top-level keys."""
        flat = db_init.flatten_entry(sample_recommendation)

        assert flat["created_at"] == "2026-02-08T12:00:00Z"
        assert flat["updated_at"] == "2026-02-08T12:00:00Z"
        assert flat["source"] == "Test RSS Source"

    def test_handles_missing_metadata(self):
        """Entry without metadata should use empty defaults."""
        entry = {
            "id": "test-id",
            "service_name": "s3",
            "scenario": "test",
            "risk_detail": "security",
        }
        flat = db_init.flatten_entry(entry)

        assert flat["created_at"] is None
        assert flat["updated_at"] is None
        assert flat["source"] is None
        assert flat["contributors"] == "[]"

    def test_json_fields_serialized(self, sample_recommendation):
        """Array fields should be serialized as JSON strings."""
        flat = db_init.flatten_entry(sample_recommendation)

        assert isinstance(flat["references"], str)
        refs = json.loads(flat["references"])
        assert isinstance(refs, list)

        assert isinstance(flat["tags"], str)
        tags = json.loads(flat["tags"])
        assert isinstance(tags, list)
        assert "versioning" in tags

        assert isinstance(flat["contributors"], str)
        contributors = json.loads(flat["contributors"])
        assert "ingest-pipeline" in contributors

    def test_handles_missing_optional_fields(self):
        """Entry with missing optional fields should get None values."""
        entry = {
            "id": "test-id",
            "service_name": "ec2",
            "scenario": "test scenario",
            "risk_detail": "cost",
        }
        flat = db_init.flatten_entry(entry)

        assert flat["output_notes"] is None
        assert flat["notes"] is None
        assert flat["pattern_implementation_guidance"] is None
        assert flat["alert_criteria"] is None


class TestDatabaseCreation:
    def _create_db(self, tmp_path, tmp_data_dir):
        """Helper: create a DuckDB database using db-init with patched paths."""
        db_path = tmp_path / "test.duckdb"
        data_dir = tmp_data_dir / "by-service"

        with patch.object(db_init, "DATA_DIR", data_dir), \
             patch.object(db_init, "DB_PATH", db_path):
            db_init.create_database()

        return db_path

    def test_creates_table(self, tmp_path, tmp_data_dir):
        """Database should contain a 'recommendations' table."""
        db_path = self._create_db(tmp_path, tmp_data_dir)

        conn = duckdb.connect(str(db_path), read_only=True)
        tables = conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_name = 'recommendations'"
        ).fetchall()
        conn.close()

        assert len(tables) == 1
        assert tables[0][0] == "recommendations"

    def test_creates_views(self, tmp_path, tmp_data_dir):
        """Database should contain the summary views."""
        db_path = self._create_db(tmp_path, tmp_data_dir)

        conn = duckdb.connect(str(db_path), read_only=True)
        views = conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_type = 'VIEW'"
        ).fetchall()
        conn.close()

        view_names = {v[0] for v in views}
        assert "summary_by_service" in view_names
        assert "summary_by_category" in view_names
        assert "summary_by_priority" in view_names
        assert "summary_by_risk_type" in view_names

    def test_inserts_data(self, tmp_path, tmp_data_dir):
        """Database should contain the entries from the data files."""
        db_path = self._create_db(tmp_path, tmp_data_dir)

        conn = duckdb.connect(str(db_path), read_only=True)
        count = conn.execute("SELECT COUNT(*) FROM recommendations").fetchone()[0]
        conn.close()

        # tmp_data_dir has s3.json with 2 entries
        assert count == 2

    def test_data_integrity(self, tmp_path, tmp_data_dir):
        """Verify specific data fields are stored correctly."""
        db_path = self._create_db(tmp_path, tmp_data_dir)

        conn = duckdb.connect(str(db_path), read_only=True)
        rows = conn.execute(
            "SELECT id, service_name, risk_detail FROM recommendations ORDER BY id"
        ).fetchall()
        conn.close()

        assert len(rows) == 2
        # Both entries should be s3 with security risk
        for row in rows:
            assert row[1] == "s3"
            assert row[2] == "security"

    def test_summary_by_service_view(self, tmp_path, tmp_data_dir):
        """The summary_by_service view should aggregate correctly."""
        db_path = self._create_db(tmp_path, tmp_data_dir)

        conn = duckdb.connect(str(db_path), read_only=True)
        rows = conn.execute("SELECT * FROM summary_by_service").fetchall()
        conn.close()

        assert len(rows) == 1
        assert rows[0][0] == "s3"
        assert rows[0][1] == 2


class TestDbQuery:
    @pytest.fixture
    def populated_db(self, tmp_path, sample_recommendation):
        """Create an in-memory DuckDB with test data and return a connection."""
        conn = duckdb.connect(":memory:")

        # Create table
        conn.execute("""
            CREATE TABLE recommendations (
                id VARCHAR PRIMARY KEY,
                service_name VARCHAR,
                scenario VARCHAR,
                alert_criteria VARCHAR,
                recommendation_action VARCHAR,
                risk_detail VARCHAR,
                build_priority INTEGER,
                action_value INTEGER,
                effort_level INTEGER,
                risk_value INTEGER,
                recommendation_description_detailed VARCHAR,
                category VARCHAR,
                output_notes VARCHAR,
                notes VARCHAR,
                pattern_implementation_guidance VARCHAR,
                created_at VARCHAR,
                updated_at VARCHAR,
                source VARCHAR,
                "references" JSON,
                tags JSON,
                architectural_patterns JSON,
                detection_methods JSON,
                remediation_examples JSON,
                compliance_mappings JSON,
                contributors JSON
            )
        """)

        # Insert sample recommendation
        flat = db_init.flatten_entry(sample_recommendation)
        conn.execute(
            "INSERT INTO recommendations VALUES (" + ", ".join(["?"] * 25) + ")",
            list(flat.values()),
        )

        # Insert a second entry for richer query testing
        rec2 = sample_recommendation.copy()
        rec2["id"] = "b2c3d4e5-f6a7-8901-bcde-f23456789012"
        rec2["service_name"] = "ec2"
        rec2["scenario"] = "EC2 instance without encryption"
        rec2["risk_detail"] = "security"
        rec2["category"] = "compute"
        rec2["recommendation_action"] = "Enable EBS encryption on EC2 instances"
        rec2["metadata"] = {
            "created_at": "2026-02-08T12:00:00Z",
            "updated_at": "2026-02-08T12:00:00Z",
            "contributors": ["ingest-pipeline"],
            "source": "Test Source",
        }
        flat2 = db_init.flatten_entry(rec2)
        conn.execute(
            "INSERT INTO recommendations VALUES (" + ", ".join(["?"] * 25) + ")",
            list(flat2.values()),
        )

        # Create summary views
        conn.execute("""
            CREATE VIEW summary_by_service AS
            SELECT service_name, COUNT(*) as count
            FROM recommendations GROUP BY service_name ORDER BY count DESC
        """)
        conn.execute("""
            CREATE VIEW summary_by_category AS
            SELECT category, COUNT(*) as count
            FROM recommendations WHERE category IS NOT NULL
            GROUP BY category ORDER BY count DESC
        """)
        conn.execute("""
            CREATE VIEW summary_by_priority AS
            SELECT build_priority, COUNT(*) as count
            FROM recommendations WHERE build_priority IS NOT NULL
            GROUP BY build_priority ORDER BY build_priority
        """)
        conn.execute("""
            CREATE VIEW summary_by_risk_type AS
            SELECT
                CASE
                    WHEN risk_detail LIKE '%cost%' THEN 'cost'
                    WHEN risk_detail LIKE '%security%' THEN 'security'
                    WHEN risk_detail LIKE '%performance%' THEN 'performance'
                    WHEN risk_detail LIKE '%reliability%' THEN 'reliability'
                    WHEN risk_detail LIKE '%operations%' THEN 'operations'
                    ELSE 'other'
                END as risk_type,
                COUNT(*) as count
            FROM recommendations GROUP BY risk_type ORDER BY count DESC
        """)

        yield conn
        conn.close()

    def test_summary_runs(self, populated_db, capsys):
        """summary() should print summary statistics without error."""
        db_query.summary(populated_db)
        captured = capsys.readouterr()

        assert "Total Recommendations: 2" in captured.out
        assert "By Service:" in captured.out
        assert "s3" in captured.out
        assert "ec2" in captured.out

    def test_search_finds_match(self, populated_db, capsys):
        """search() should find entries matching the search term."""
        db_query.search(populated_db, "encryption")
        captured = capsys.readouterr()

        assert "encryption" in captured.out.lower()
        # Should find at least the EC2 entry
        assert "ec2" in captured.out.lower() or "s3" in captured.out.lower()

    def test_search_no_match(self, populated_db, capsys):
        """search() should handle no results gracefully."""
        db_query.search(populated_db, "zzz_nonexistent_zzz")
        captured = capsys.readouterr()

        assert "Found 0 results" in captured.out

    def test_service_filter(self, populated_db, capsys):
        """service() should filter results by service name."""
        db_query.service(populated_db, "s3")
        captured = capsys.readouterr()

        assert "s3" in captured.out.lower()
        assert "Total: 1" in captured.out

    def test_service_filter_no_results(self, populated_db, capsys):
        """service() should handle services with no results."""
        db_query.service(populated_db, "nonexistent-service")
        captured = capsys.readouterr()

        assert "Total: 0" in captured.out

    def test_search_matches_recommendation_action(self, populated_db, capsys):
        """search() should also match against recommendation_action."""
        db_query.search(populated_db, "Enable EBS")
        captured = capsys.readouterr()

        assert "Found" in captured.out
        # Should find the EC2 entry via its recommendation_action
        assert "1 result" in captured.out or "ec2" in captured.out.lower()
