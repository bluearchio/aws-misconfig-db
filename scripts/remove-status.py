#!/usr/bin/env python3
"""
Remove the 'status' field from all recommendations.
All recommendations are considered 'done' by default.
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data" / "by-service"


def remove_status_from_file(filepath):
    """Remove status field from all entries in a file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    modified = 0
    if 'misconfigurations' in data:
        for entry in data['misconfigurations']:
            if 'status' in entry:
                del entry['status']
                modified += 1

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return modified


def main():
    total_modified = 0
    files_processed = 0

    for json_file in sorted(DATA_DIR.glob("*.json")):
        modified = remove_status_from_file(json_file)
        if modified > 0:
            print(f"  {json_file.name}: removed status from {modified} entries")
            total_modified += modified
        files_processed += 1

    print(f"\nProcessed {files_processed} files")
    print(f"Removed status field from {total_modified} entries")


if __name__ == "__main__":
    main()
