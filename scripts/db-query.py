#!/usr/bin/env python3
"""
Query helper for AWS Misconfiguration DuckDB database.
Provides common queries and an interactive mode.
"""

import duckdb
import argparse
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "db" / "recommendations.duckdb"


def get_connection():
    """Get database connection."""
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        print("Run: python3 scripts/db-init.py")
        exit(1)
    return duckdb.connect(str(DB_PATH), read_only=True)


def summary(conn):
    """Print full summary statistics."""
    print("=" * 60)
    print("AWS Misconfiguration Database - Summary Statistics")
    print("=" * 60)

    total = conn.execute("SELECT COUNT(*) FROM recommendations").fetchone()[0]
    print(f"\nTotal Recommendations: {total}\n")

    print("By Service:")
    print("-" * 40)
    for row in conn.execute("SELECT * FROM summary_by_service").fetchall():
        print(f"  {row[0]:20} {row[1]:>5}")

    print("\nBy Risk Type:")
    print("-" * 40)
    for row in conn.execute("SELECT * FROM summary_by_risk_type").fetchall():
        print(f"  {row[0]:20} {row[1]:>5}")

    print("\nBy Category:")
    print("-" * 40)
    for row in conn.execute("SELECT * FROM summary_by_category").fetchall():
        print(f"  {row[0]:20} {row[1]:>5}")

    print("\nBy Priority:")
    print("-" * 40)
    for row in conn.execute("SELECT * FROM summary_by_priority").fetchall():
        print(f"  Priority {row[0]}:          {row[1]:>5}")


def search(conn, term):
    """Search recommendations by term."""
    results = conn.execute("""
        SELECT service_name, scenario, risk_detail
        FROM recommendations
        WHERE scenario ILIKE ? OR recommendation_action ILIKE ?
        LIMIT 20
    """, [f'%{term}%', f'%{term}%']).fetchall()

    print(f"\nSearch results for '{term}':")
    print("-" * 60)
    for row in results:
        print(f"[{row[0]}] {row[1][:70]}...")
        print(f"  Risk: {row[2]}\n")

    print(f"Found {len(results)} results (showing max 20)")


def service(conn, service_name):
    """List recommendations for a specific service."""
    results = conn.execute("""
        SELECT scenario, risk_detail, build_priority
        FROM recommendations
        WHERE service_name = ?
        ORDER BY build_priority NULLS LAST
    """, [service_name]).fetchall()

    print(f"\nRecommendations for {service_name}:")
    print("-" * 60)
    for row in results:
        priority = f"P{row[2]}" if row[2] is not None else "P?"
        print(f"[{priority}] {row[0][:65]}...")
        print(f"  Risk: {row[1]}\n")

    print(f"Total: {len(results)} recommendations")


def patterns(conn):
    """Show architectural patterns in the database."""
    results = conn.execute("""
        SELECT
            json_extract_string(p.pattern, '$.pattern_name') as pattern_name,
            COUNT(*) as count
        FROM recommendations r,
             LATERAL unnest(json_extract(r.architectural_patterns, '$[*]')) as p(pattern)
        WHERE r.architectural_patterns != '[]'
        GROUP BY pattern_name
        ORDER BY count DESC
    """).fetchall()

    print("\nArchitectural Patterns:")
    print("-" * 40)
    for row in results:
        print(f"  {row[0]:35} {row[1]:>5}")


def sql(conn, query):
    """Execute raw SQL query."""
    try:
        result = conn.execute(query)
        print(result.fetchdf().to_string())
    except Exception as e:
        print(f"Error: {e}")


def interactive(conn):
    """Interactive SQL mode."""
    print("DuckDB Interactive Mode")
    print("Type SQL queries or 'exit' to quit")
    print("Tables: recommendations")
    print("Views: summary_by_service, summary_by_status, summary_by_category, summary_by_priority")
    print("-" * 60)

    while True:
        try:
            query = input("\nsql> ").strip()
            if query.lower() in ('exit', 'quit', 'q'):
                break
            if query:
                sql(conn, query)
        except (KeyboardInterrupt, EOFError):
            break

    print("\nGoodbye!")


def main():
    parser = argparse.ArgumentParser(
        description="Query AWS Misconfiguration DuckDB database"
    )
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Summary command
    subparsers.add_parser('summary', help='Show full summary statistics')

    # Search command
    search_parser = subparsers.add_parser('search', help='Search recommendations')
    search_parser.add_argument('term', help='Search term')

    # Service command
    service_parser = subparsers.add_parser('service', help='List recommendations for a service')
    service_parser.add_argument('name', help='Service name (e.g., ec2, s3, lambda)')

    # Patterns command
    subparsers.add_parser('patterns', help='Show architectural patterns')

    # SQL command
    sql_parser = subparsers.add_parser('sql', help='Execute raw SQL')
    sql_parser.add_argument('query', help='SQL query')

    # Interactive command
    subparsers.add_parser('interactive', aliases=['i'], help='Interactive SQL mode')

    args = parser.parse_args()
    conn = get_connection()

    if args.command == 'summary':
        summary(conn)
    elif args.command == 'search':
        search(conn, args.term)
    elif args.command == 'service':
        service(conn, args.name)
    elif args.command == 'patterns':
        patterns(conn)
    elif args.command == 'sql':
        sql(conn, args.query)
    elif args.command in ('interactive', 'i'):
        interactive(conn)
    else:
        # Default to summary
        summary(conn)

    conn.close()


if __name__ == "__main__":
    main()
