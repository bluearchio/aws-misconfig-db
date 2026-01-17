#!/usr/bin/env python3
"""
Initialize DuckDB database from AWS Misconfiguration recommendation files.
Creates a queryable database from data/by-service/*.json files.
"""

import json
import duckdb
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data" / "by-service"
DB_PATH = BASE_DIR / "db" / "recommendations.duckdb"


def load_all_entries():
    """Load all recommendations from by-service JSON files."""
    entries = []
    for json_file in sorted(DATA_DIR.glob("*.json")):
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if 'misconfigurations' in data:
                entries.extend(data['misconfigurations'])
    return entries


def flatten_entry(entry):
    """Flatten nested fields for database storage."""
    flat = {
        'id': entry.get('id'),
        'status': entry.get('status'),
        'service_name': entry.get('service_name'),
        'scenario': entry.get('scenario'),
        'alert_criteria': entry.get('alert_criteria'),
        'recommendation_action': entry.get('recommendation_action'),
        'risk_detail': entry.get('risk_detail'),
        'build_priority': entry.get('build_priority'),
        'action_value': entry.get('action_value'),
        'effort_level': entry.get('effort_level'),
        'risk_value': entry.get('risk_value'),
        'recommendation_description_detailed': entry.get('recommendation_description_detailed'),
        'category': entry.get('category'),
        'output_notes': entry.get('output_notes'),
        'notes': entry.get('notes'),
        'pattern_implementation_guidance': entry.get('pattern_implementation_guidance'),
        # Flatten metadata
        'created_at': entry.get('metadata', {}).get('created_at'),
        'updated_at': entry.get('metadata', {}).get('updated_at'),
        'source': entry.get('metadata', {}).get('source'),
        # JSON fields stored as strings
        'references': json.dumps(entry.get('references', [])),
        'tags': json.dumps(entry.get('tags', [])),
        'architectural_patterns': json.dumps(entry.get('architectural_patterns', [])),
        'detection_methods': json.dumps(entry.get('detection_methods', [])),
        'remediation_examples': json.dumps(entry.get('remediation_examples', [])),
        'compliance_mappings': json.dumps(entry.get('compliance_mappings', [])),
        'contributors': json.dumps(entry.get('metadata', {}).get('contributors', [])),
    }
    return flat


def create_database():
    """Create DuckDB database with recommendations table."""
    # Remove existing database
    if DB_PATH.exists():
        DB_PATH.unlink()

    # Load entries
    print("Loading recommendations from data/by-service/*.json...")
    entries = load_all_entries()
    print(f"Loaded {len(entries)} entries")

    # Flatten entries
    flat_entries = [flatten_entry(e) for e in entries]

    # Create database
    print(f"\nCreating DuckDB database at {DB_PATH}...")
    conn = duckdb.connect(str(DB_PATH))

    # Create main recommendations table
    conn.execute("""
        CREATE TABLE recommendations (
            id VARCHAR PRIMARY KEY,
            status VARCHAR,
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

    # Insert data
    for entry in flat_entries:
        conn.execute("""
            INSERT INTO recommendations VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
        """, list(entry.values()))

    # Create summary views
    print("Creating summary views...")

    conn.execute("""
        CREATE VIEW summary_by_service AS
        SELECT service_name, COUNT(*) as count
        FROM recommendations
        GROUP BY service_name
        ORDER BY count DESC
    """)

    conn.execute("""
        CREATE VIEW summary_by_status AS
        SELECT status, COUNT(*) as count
        FROM recommendations
        GROUP BY status
        ORDER BY count DESC
    """)

    conn.execute("""
        CREATE VIEW summary_by_category AS
        SELECT category, COUNT(*) as count
        FROM recommendations
        WHERE category IS NOT NULL
        GROUP BY category
        ORDER BY count DESC
    """)

    conn.execute("""
        CREATE VIEW summary_by_priority AS
        SELECT build_priority, COUNT(*) as count
        FROM recommendations
        WHERE build_priority IS NOT NULL
        GROUP BY build_priority
        ORDER BY build_priority
    """)

    # Commit and show stats
    conn.commit()

    print("\n" + "=" * 60)
    print("Database created successfully!")
    print("=" * 60)

    # Show summary
    print("\n📊 Summary Statistics:\n")

    print("By Service (Top 10):")
    result = conn.execute("SELECT * FROM summary_by_service LIMIT 10").fetchall()
    for row in result:
        print(f"  {row[0]}: {row[1]}")

    print("\nBy Status:")
    result = conn.execute("SELECT * FROM summary_by_status").fetchall()
    for row in result:
        print(f"  {row[0]}: {row[1]}")

    print("\nBy Priority:")
    result = conn.execute("SELECT * FROM summary_by_priority").fetchall()
    for row in result:
        print(f"  Priority {row[0]}: {row[1]}")

    total = conn.execute("SELECT COUNT(*) FROM recommendations").fetchone()[0]
    print(f"\nTotal recommendations: {total}")

    conn.close()
    print(f"\n✓ Database saved to: {DB_PATH}")


def main():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    create_database()


if __name__ == "__main__":
    main()
