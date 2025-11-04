#!/usr/bin/env python3
"""
CSV Import Script for AWS Misconfiguration Database
Converts CSV data to structured JSON format according to the schema
"""

import csv
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict
import argparse


def generate_uuid() -> str:
    """Generate a UUID for misconfiguration entry"""
    return str(uuid.uuid4())


def clean_value(value: str) -> Any:
    """Clean and normalize CSV values"""
    if not value or value.strip() == "" or value.strip().upper() == "TK":
        return None
    return value.strip()


def safe_int(value: str) -> Any:
    """Safely convert string to int, return None if not possible"""
    cleaned = clean_value(value)
    if cleaned is None:
        return None
    try:
        return int(cleaned)
    except (ValueError, TypeError):
        return None


def sanitize_filename(name: str) -> str:
    """Sanitize a string to be a valid filename"""
    if not name:
        return "unknown"
    # Replace problematic characters
    sanitized = name.replace("/", "-").replace("\\", "-").replace(" ", "-")
    # Remove any remaining problematic characters
    sanitized = "".join(c for c in sanitized if c.isalnum() or c in ["-", "_", "."])
    return sanitized.lower()


def parse_risk_detail(risk_detail: str) -> str:
    """Parse and normalize risk detail field"""
    if not risk_detail:
        return "operations"

    # Normalize common variations
    risk_detail = risk_detail.strip().lower()

    # Handle multiple risk types
    if "," in risk_detail:
        parts = [p.strip() for p in risk_detail.split(",")]
        return ", ".join(parts)

    return risk_detail


def parse_references(link1: str, link2: str, link3: str) -> List[str]:
    """Extract valid reference URLs from link columns"""
    references = []
    for link in [link1, link2, link3]:
        cleaned = clean_value(link)
        if cleaned and cleaned.startswith("http"):
            references.append(cleaned)
    return references


def parse_category(category: str) -> str:
    """Parse and normalize category field"""
    if not category:
        return None

    # Map common variations
    category_map = {
        "compute": "compute",
        "networking": "networking",
        "network": "networking",
        "database": "database",
        "storage": "storage",
        "security": "security"
    }

    return category_map.get(category.lower().strip(), category.strip())


def convert_csv_to_json(csv_path: str, output_dir: Path) -> Dict[str, List[Dict]]:
    """
    Convert CSV file to JSON entries organized by service

    Args:
        csv_path: Path to input CSV file
        output_dir: Base output directory for JSON files

    Returns:
        Dictionary mapping service names to lists of entries
    """
    entries_by_service = defaultdict(list)
    entries_by_category = defaultdict(list)
    all_entries = []

    timestamp = datetime.utcnow().isoformat() + "Z"

    with open(csv_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            # Skip empty rows
            if not any(row.values()):
                continue

            # Extract and clean data
            service_name = clean_value(row.get('service_name'))
            scenario = clean_value(row.get('scenario'))

            # Skip rows without essential data
            if not service_name and not scenario:
                continue

            # Build entry according to schema
            entry = {
                "id": generate_uuid(),
                "status": clean_value(row.get('status')) or "open",
                "service_name": service_name or "general",
                "scenario": scenario or "",
                "alert_criteria": clean_value(row.get('alert_criteria')) or "",
                "recommendation_action": clean_value(row.get('recommendation_action')) or "",
                "risk_detail": parse_risk_detail(row.get('risk_detail')),
                "build_priority": safe_int(row.get('build_priority', 0)),
                "action_value": safe_int(row.get('action_value')),
                "effort_level": safe_int(row.get('effort_level')),
                "risk_value": safe_int(row.get('risk_value')),
                "recommendation_description_detailed": clean_value(row.get('recommendation_description_detailed')) or "",
                "category": parse_category(row.get('rec_category')),
                "output_notes": clean_value(row.get('output (pro / con) ')),
                "notes": clean_value(row.get('notes')),
                "references": parse_references(
                    row.get('link_1', ''),
                    row.get('link_2', ''),
                    row.get('link_3', '')
                ),
                "metadata": {
                    "created_at": timestamp,
                    "updated_at": timestamp,
                    "contributors": ["initial-import"],
                    "source": "Initial CSV Import"
                },
                "tags": []
            }

            # Add to service collection
            service = entry["service_name"]
            entries_by_service[service].append(entry)

            # Add to category collection
            if entry["category"]:
                entries_by_category[entry["category"]].append(entry)

            # Add to risk type collection
            if entry["risk_detail"]:
                risk_types = [r.strip() for r in entry["risk_detail"].split(",")]
                for risk_type in risk_types:
                    entries_by_category[risk_type].append(entry)

            all_entries.append(entry)

    # Write service-based files
    service_dir = output_dir / "by-service"
    service_dir.mkdir(parents=True, exist_ok=True)

    for service, entries in entries_by_service.items():
        output_file = service_dir / f"{sanitize_filename(service)}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "service": service,
                "count": len(entries),
                "misconfigurations": entries
            }, f, indent=2, ensure_ascii=False)
        print(f"✓ Created {output_file} with {len(entries)} entries")

    # Write category-based files
    category_dir = output_dir / "by-category"
    category_dir.mkdir(parents=True, exist_ok=True)

    for category, entries in entries_by_category.items():
        output_file = category_dir / f"{sanitize_filename(category)}.json"
        # Remove duplicates while preserving order
        seen = set()
        unique_entries = []
        for entry in entries:
            if entry["id"] not in seen:
                seen.add(entry["id"])
                unique_entries.append(entry)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "category": category,
                "count": len(unique_entries),
                "misconfigurations": unique_entries
            }, f, indent=2, ensure_ascii=False)
        print(f"✓ Created {output_file} with {len(unique_entries)} entries")

    # Write unified file
    all_file = output_dir / "all-misconfigs.json"
    with open(all_file, 'w', encoding='utf-8') as f:
        json.dump({
            "version": "1.0.0",
            "generated_at": timestamp,
            "total_count": len(all_entries),
            "services": list(entries_by_service.keys()),
            "categories": list(set(entries_by_category.keys())),
            "misconfigurations": all_entries
        }, f, indent=2, ensure_ascii=False)
    print(f"✓ Created {all_file} with {len(all_entries)} total entries")

    return entries_by_service


def generate_summary(entries_by_service: Dict[str, List[Dict]]) -> Dict[str, Any]:
    """Generate summary statistics"""
    total_entries = sum(len(entries) for entries in entries_by_service.values())

    status_counts = defaultdict(int)
    risk_counts = defaultdict(int)

    for entries in entries_by_service.values():
        for entry in entries:
            status_counts[entry.get("status", "unknown")] += 1
            risk_detail = entry.get("risk_detail")
            if risk_detail:
                for risk in risk_detail.split(","):
                    risk_counts[risk.strip()] += 1

    return {
        "total_entries": total_entries,
        "total_services": len(entries_by_service),
        "status_breakdown": dict(status_counts),
        "risk_breakdown": dict(risk_counts),
        "services": {service: len(entries) for service, entries in entries_by_service.items()}
    }


def main():
    parser = argparse.ArgumentParser(
        description="Import AWS misconfigurations from CSV to JSON"
    )
    parser.add_argument(
        "csv_file",
        help="Path to input CSV file"
    )
    parser.add_argument(
        "--output-dir",
        default="data",
        help="Output directory for JSON files (default: data)"
    )

    args = parser.parse_args()

    csv_path = Path(args.csv_file)
    output_dir = Path(args.output_dir)

    if not csv_path.exists():
        print(f"Error: CSV file not found: {csv_path}")
        return 1

    print(f"Importing data from {csv_path}...")
    print(f"Output directory: {output_dir}")
    print()

    entries_by_service = convert_csv_to_json(str(csv_path), output_dir)

    print()
    print("=" * 60)
    print("Import Summary")
    print("=" * 60)

    summary = generate_summary(entries_by_service)
    print(f"Total Entries: {summary['total_entries']}")
    print(f"Total Services: {summary['total_services']}")
    print()

    print("Status Breakdown:")
    for status, count in sorted(summary['status_breakdown'].items()):
        print(f"  {status}: {count}")
    print()

    print("Risk Type Breakdown:")
    for risk, count in sorted(summary['risk_breakdown'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {risk}: {count}")
    print()

    print("Top Services:")
    for service, count in sorted(summary['services'].items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {service}: {count}")

    print()
    print("✓ Import completed successfully!")

    return 0


if __name__ == "__main__":
    exit(main())
