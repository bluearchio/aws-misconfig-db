#!/usr/bin/env python3
"""
Generate documentation summary from AWS Misconfiguration Database.
Reads from data/by-service/*.json (the single source of truth) and generates docs/SUMMARY.md.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
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


def update_readme_counts(total_recs: int, num_services: int, readme_path: Path | None = None) -> bool:
    """Update hardcoded recommendation and service counts in README.md.

    Finds and replaces counts in two locations:
    1. The ASCII banner line (e.g. "🔥 323 Recommendations • 46 Services 🔥")
    2. The footer line (e.g. "🔥 323 recommendations • 46 services")

    Args:
        total_recs: Total number of recommendations.
        num_services: Total number of services.
        readme_path: Path to README.md. Defaults to project root README.md.

    Returns:
        True if any replacements were made, False otherwise.
    """
    if readme_path is None:
        readme_path = Path(__file__).parent.parent / "README.md"

    if not readme_path.exists():
        print(f"Warning: README.md not found at {readme_path}")
        return False

    content = readme_path.read_text(encoding="utf-8")
    original = content

    # Pattern 1: Banner line (capitalized "Recommendations" and "Services")
    banner_pattern = r"🔥 \d+ Recommendations • \d+ Services 🔥"
    banner_replacement = f"🔥 {total_recs} Recommendations • {num_services} Services 🔥"
    content = re.sub(banner_pattern, banner_replacement, content)

    # Pattern 2: Footer line (lowercase "recommendations" and "services")
    footer_pattern = r"🔥 \d+ recommendations • \d+ services"
    footer_replacement = f"🔥 {total_recs} recommendations • {num_services} services"
    content = re.sub(footer_pattern, footer_replacement, content)

    if content != original:
        readme_path.write_text(content, encoding="utf-8")
        print(f"✓ Updated README.md counts: {total_recs} recommendations, {num_services} services")
        return True
    else:
        print("README.md counts already up to date")
        return False


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
    parser.add_argument(
        "--skip-website-sync",
        action="store_true",
        help="Do not update the sibling bluearch-website Governance Hub catalog",
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

    # Update README.md hardcoded counts
    update_readme_counts(stats['total_entries'], len(stats['by_service']))

    if not args.skip_website_sync:
        sync_script = Path(__file__).parent / "sync_website_governance.py"
        website_output = (
            Path(__file__).parent.parent.parent
            / "bluearch-website"
            / "frontend"
            / "app"
            / "src"
            / "data"
            / "governanceCatalog.json"
        )
        if sync_script.exists() and website_output.parent.exists():
            subprocess.run([sys.executable, str(sync_script), "--output", str(website_output)], check=True)

    return 0


if __name__ == "__main__":
    exit(main())
