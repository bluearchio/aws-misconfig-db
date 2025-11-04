#!/usr/bin/env python3
"""
Generation Script for AWS Misconfiguration Database
Generates aggregated files, summaries, and documentation from individual entries
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict
from datetime import datetime
import argparse


def load_all_entries(data_dir: Path) -> List[Dict[str, Any]]:
    """Load all misconfiguration entries from by-service directory"""
    entries = []
    service_dir = data_dir / "by-service"

    if not service_dir.exists():
        print(f"Warning: Service directory not found: {service_dir}")
        return entries

    for json_file in service_dir.glob("*.json"):
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if 'misconfigurations' in data:
                entries.extend(data['misconfigurations'])

    return entries


def generate_unified_file(entries: List[Dict[str, Any]], output_path: Path):
    """Generate unified file with all misconfigurations"""
    services = set()
    categories = set()

    for entry in entries:
        if entry.get('service_name'):
            services.add(entry['service_name'])
        if entry.get('category'):
            categories.add(entry['category'])

    unified_data = {
        "version": "1.0.0",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_count": len(entries),
        "services": sorted(services),
        "categories": sorted(categories),
        "misconfigurations": entries
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(unified_data, f, indent=2, ensure_ascii=False)

    print(f"✓ Generated {output_path} with {len(entries)} entries")


def generate_category_files(entries: List[Dict[str, Any]], output_dir: Path):
    """Generate files organized by category and risk type"""
    entries_by_category = defaultdict(list)

    for entry in entries:
        # Add to category collection
        if entry.get('category'):
            entries_by_category[entry['category']].append(entry)

        # Add to risk type collection
        if entry.get('risk_detail'):
            risk_types = [r.strip() for r in entry['risk_detail'].split(",")]
            for risk_type in risk_types:
                entries_by_category[risk_type].append(entry)

    output_dir.mkdir(parents=True, exist_ok=True)

    for category, cat_entries in entries_by_category.items():
        # Remove duplicates while preserving order
        seen = set()
        unique_entries = []
        for entry in cat_entries:
            if entry["id"] not in seen:
                seen.add(entry["id"])
                unique_entries.append(entry)

        output_file = output_dir / f"{sanitize_filename(category)}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "category": category,
                "count": len(unique_entries),
                "misconfigurations": unique_entries
            }, f, indent=2, ensure_ascii=False)

        print(f"✓ Generated {output_file} with {len(unique_entries)} entries")


def sanitize_filename(name: str) -> str:
    """Sanitize a string to be a valid filename"""
    if not name:
        return "unknown"
    sanitized = name.replace("/", "-").replace("\\", "-").replace(" ", "-")
    sanitized = "".join(c for c in sanitized if c.isalnum() or c in ["-", "_", "."])
    return sanitized.lower()


def generate_summary_stats(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate summary statistics"""
    stats = {
        "total_entries": len(entries),
        "by_status": defaultdict(int),
        "by_service": defaultdict(int),
        "by_category": defaultdict(int),
        "by_risk_type": defaultdict(int),
        "by_priority": defaultdict(int)
    }

    for entry in entries:
        # Count by status
        status = entry.get('status', 'unknown')
        stats['by_status'][status] += 1

        # Count by service
        service = entry.get('service_name', 'unknown')
        stats['by_service'][service] += 1

        # Count by category
        category = entry.get('category')
        if category:
            stats['by_category'][category] += 1

        # Count by risk type
        risk_detail = entry.get('risk_detail')
        if risk_detail:
            for risk in risk_detail.split(','):
                stats['by_risk_type'][risk.strip()] += 1

        # Count by priority
        priority = entry.get('build_priority')
        if priority is not None:
            stats['by_priority'][str(priority)] += 1

    # Convert defaultdicts to regular dicts for JSON serialization
    stats['by_status'] = dict(stats['by_status'])
    stats['by_service'] = dict(stats['by_service'])
    stats['by_category'] = dict(stats['by_category'])
    stats['by_risk_type'] = dict(stats['by_risk_type'])
    stats['by_priority'] = dict(stats['by_priority'])

    return stats


def generate_summary_file(stats: Dict[str, Any], output_path: Path):
    """Generate summary statistics file"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    print(f"✓ Generated {output_path}")


def generate_markdown_summary(stats: Dict[str, Any], entries: List[Dict[str, Any]], output_path: Path):
    """Generate markdown summary document"""
    lines = [
        "# AWS Misconfiguration Database - Summary",
        "",
        f"**Total Misconfigurations:** {stats['total_entries']}",
        f"**Last Updated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
        "",
        "## Overview",
        "",
        "This database contains AWS misconfiguration entries covering security, cost optimization,",
        "performance, reliability, and operational best practices.",
        "",
        "## Statistics",
        "",
        "### By Status",
        "",
        "| Status | Count |",
        "| ------ | ----- |",
    ]

    for status, count in sorted(stats['by_status'].items()):
        lines.append(f"| {status} | {count} |")

    lines.extend([
        "",
        "### By Risk Type",
        "",
        "| Risk Type | Count |",
        "| --------- | ----- |",
    ])

    for risk, count in sorted(stats['by_risk_type'].items(), key=lambda x: x[1], reverse=True):
        lines.append(f"| {risk} | {count} |")

    lines.extend([
        "",
        "### Top 10 Services",
        "",
        "| Service | Count |",
        "| ------- | ----- |",
    ])

    sorted_services = sorted(stats['by_service'].items(), key=lambda x: x[1], reverse=True)[:10]
    for service, count in sorted_services:
        lines.append(f"| {service} | {count} |")

    lines.extend([
        "",
        "### By Category",
        "",
        "| Category | Count |",
        "| -------- | ----- |",
    ])

    for category, count in sorted(stats['by_category'].items(), key=lambda x: x[1], reverse=True):
        lines.append(f"| {category} | {count} |")

    lines.extend([
        "",
        "### By Priority",
        "",
        "| Priority Level | Count |",
        "| -------------- | ----- |",
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
        "See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines on how to contribute new",
        "misconfiguration entries.",
        ""
    ])

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"✓ Generated {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate aggregated files and summaries for AWS misconfiguration database"
    )
    parser.add_argument(
        "--data-dir",
        default="data",
        help="Data directory containing JSON files (default: data)"
    )
    parser.add_argument(
        "--docs-dir",
        default="docs",
        help="Documentation directory for output files (default: docs)"
    )

    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    docs_dir = Path(args.docs_dir)

    if not data_dir.exists():
        print(f"Error: Data directory not found: {data_dir}")
        return 1

    print("Loading misconfiguration entries...")
    entries = load_all_entries(data_dir)

    if not entries:
        print("No entries found to process")
        return 1

    print(f"Loaded {len(entries)} entries")
    print()

    # Generate unified file
    print("Generating unified file...")
    unified_path = data_dir / "all-misconfigs.json"
    generate_unified_file(entries, unified_path)
    print()

    # Generate category files
    print("Generating category files...")
    category_dir = data_dir / "by-category"
    generate_category_files(entries, category_dir)
    print()

    # Generate statistics
    print("Generating statistics...")
    stats = generate_summary_stats(entries)

    stats_path = data_dir / "summary-stats.json"
    generate_summary_file(stats, stats_path)
    print()

    # Generate markdown summary
    print("Generating markdown summary...")
    docs_dir.mkdir(parents=True, exist_ok=True)
    summary_md_path = docs_dir / "SUMMARY.md"
    generate_markdown_summary(stats, entries, summary_md_path)
    print()

    print("=" * 60)
    print("Generation completed successfully!")
    print("=" * 60)
    print(f"Total entries processed: {len(entries)}")
    print(f"Unified file: {unified_path}")
    print(f"Category files: {category_dir}")
    print(f"Statistics: {stats_path}")
    print(f"Summary: {summary_md_path}")

    return 0


if __name__ == "__main__":
    exit(main())
