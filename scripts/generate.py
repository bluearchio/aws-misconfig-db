#!/usr/bin/env python3
"""
Generate documentation summary from AWS Misconfiguration Database.
Reads from data/by-service/*.json (the single source of truth) and generates docs/SUMMARY.md.
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict
from datetime import datetime
import argparse


def load_all_entries(data_dir: Path) -> List[Dict[str, Any]]:
    """Load all misconfiguration entries from by-service directory."""
    entries = []
    service_dir = data_dir / "by-service"

    if not service_dir.exists():
        print(f"Warning: Service directory not found: {service_dir}")
        return entries

    for json_file in sorted(service_dir.glob("*.json")):
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if 'misconfigurations' in data:
                entries.extend(data['misconfigurations'])

    return entries


def generate_stats(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate summary statistics from entries."""
    stats = {
        "total_entries": len(entries),
        "by_service": defaultdict(int),
        "by_category": defaultdict(int),
        "by_risk_type": defaultdict(int),
        "by_priority": defaultdict(int)
    }

    for entry in entries:
        stats['by_service'][entry.get('service_name', 'unknown')] += 1

        if entry.get('category'):
            stats['by_category'][entry['category']] += 1

        if entry.get('risk_detail'):
            for risk in entry['risk_detail'].split(','):
                stats['by_risk_type'][risk.strip()] += 1

        if entry.get('build_priority') is not None:
            stats['by_priority'][str(entry['build_priority'])] += 1

    # Convert to regular dicts
    for key in ['by_service', 'by_category', 'by_risk_type', 'by_priority']:
        stats[key] = dict(stats[key])

    return stats


def generate_markdown_summary(stats: Dict[str, Any], output_path: Path):
    """Generate markdown summary document."""
    lines = [
        "# AWS Misconfiguration Database - Summary",
        "",
        f"**Total Recommendations:** {stats['total_entries']}",
        f"**Last Updated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
        "",
        "## Overview",
        "",
        "This database contains AWS misconfiguration recommendations covering security, cost optimization,",
        "performance, reliability, and operational best practices.",
        "",
        "**Source of Truth:** `data/by-service/*.json`",
        "",
        "## Statistics",
        "",
        "### By Risk Type",
        "",
        "| Risk Type | Count |",
        "| --------- | ----- |",
    ]

    for risk, count in sorted(stats['by_risk_type'].items(), key=lambda x: x[1], reverse=True):
        lines.append(f"| {risk} | {count} |")

    lines.extend([
        "",
        "### By Service",
        "",
        "| Service | Count |",
        "| ------- | ----- |",
    ])

    for service, count in sorted(stats['by_service'].items(), key=lambda x: x[1], reverse=True):
        lines.append(f"| {service} | {count} |")

    if stats['by_category']:
        lines.extend([
            "",
            "### By Category",
            "",
            "| Category | Count |",
            "| -------- | ----- |",
        ])

        for category, count in sorted(stats['by_category'].items(), key=lambda x: x[1], reverse=True):
            lines.append(f"| {category} | {count} |")

    if stats['by_priority']:
        lines.extend([
            "",
            "### By Priority",
            "",
            "| Priority | Count |",
            "| -------- | ----- |",
        ])

        for priority in sorted(stats['by_priority'].keys()):
            lines.append(f"| {priority} | {stats['by_priority'][priority]} |")

    lines.extend([
        "",
        "## Usage",
        "",
        "See the main [README.md](../README.md) for usage instructions and integration examples.",
        "",
        "## Contributing",
        "",
        "See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines on how to contribute new entries.",
        ""
    ])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"✓ Generated {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate documentation summary for AWS misconfiguration database"
    )
    parser.add_argument(
        "--data-dir",
        default="data",
        help="Data directory containing by-service/*.json files (default: data)"
    )
    parser.add_argument(
        "--docs-dir",
        default="docs",
        help="Documentation directory for output (default: docs)"
    )

    args = parser.parse_args()
    data_dir = Path(args.data_dir)
    docs_dir = Path(args.docs_dir)

    if not data_dir.exists():
        print(f"Error: Data directory not found: {data_dir}")
        return 1

    print("Loading entries from data/by-service/*.json...")
    entries = load_all_entries(data_dir)

    if not entries:
        print("No entries found")
        return 1

    print(f"Loaded {len(entries)} entries from {len(list((data_dir / 'by-service').glob('*.json')))} service files")

    stats = generate_stats(entries)
    summary_path = docs_dir / "SUMMARY.md"
    generate_markdown_summary(stats, summary_path)

    print(f"\nTotal: {stats['total_entries']} recommendations across {len(stats['by_service'])} services")
    return 0


if __name__ == "__main__":
    exit(main())
