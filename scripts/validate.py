#!/usr/bin/env python3
"""
Validation Script for AWS Misconfiguration Database
Validates JSON entries against the schema
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple
import argparse


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load JSON schema from file"""
    with open(schema_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load and parse JSON file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_required_fields(entry: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """Validate that all required fields are present"""
    errors = []
    required_fields = schema.get('required', [])

    for field in required_fields:
        if field not in entry or entry[field] is None or entry[field] == "":
            errors.append(f"Missing required field: {field}")

    return errors


def validate_field_types(entry: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """Validate field types match schema"""
    errors = []
    properties = schema.get('properties', {})

    for field, value in entry.items():
        if field not in properties:
            continue

        prop_schema = properties[field]
        expected_type = prop_schema.get('type')

        if value is None:
            continue

        # Handle multiple allowed types
        if isinstance(expected_type, list):
            type_valid = False
            for t in expected_type:
                if t == 'null' and value is None:
                    type_valid = True
                    break
                if validate_type(value, t):
                    type_valid = True
                    break
            if not type_valid:
                errors.append(f"Field '{field}' has invalid type. Expected one of {expected_type}, got {type(value).__name__}")
        else:
            if not validate_type(value, expected_type):
                errors.append(f"Field '{field}' has invalid type. Expected {expected_type}, got {type(value).__name__}")

    return errors


def validate_type(value: Any, expected_type: str) -> bool:
    """Check if value matches expected type"""
    type_map = {
        'string': str,
        'integer': int,
        'number': (int, float),
        'boolean': bool,
        'array': list,
        'object': dict,
        'null': type(None)
    }

    expected_python_type = type_map.get(expected_type)
    if expected_python_type is None:
        return True

    return isinstance(value, expected_python_type)


def validate_enum_values(entry: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """Validate enum field values"""
    errors = []
    properties = schema.get('properties', {})

    for field, value in entry.items():
        if field not in properties or value is None:
            continue

        prop_schema = properties[field]
        if 'enum' in prop_schema:
            allowed_values = prop_schema['enum']
            if value not in allowed_values:
                errors.append(f"Field '{field}' has invalid value '{value}'. Allowed values: {allowed_values}")

    return errors


def validate_ranges(entry: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """Validate integer ranges"""
    errors = []
    properties = schema.get('properties', {})

    for field, value in entry.items():
        if field not in properties or value is None:
            continue

        prop_schema = properties[field]

        # Check minimum
        if 'minimum' in prop_schema and isinstance(value, (int, float)):
            if value < prop_schema['minimum']:
                errors.append(f"Field '{field}' value {value} is below minimum {prop_schema['minimum']}")

        # Check maximum
        if 'maximum' in prop_schema and isinstance(value, (int, float)):
            if value > prop_schema['maximum']:
                errors.append(f"Field '{field}' value {value} exceeds maximum {prop_schema['maximum']}")

    return errors


def validate_uuid_format(entry: Dict[str, Any]) -> List[str]:
    """Validate UUID format for id field"""
    errors = []
    if 'id' in entry:
        import re
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        if not re.match(uuid_pattern, entry['id']):
            errors.append(f"Field 'id' does not match UUID format: {entry['id']}")
    return errors


def validate_entry(entry: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate a single misconfiguration entry"""
    all_errors = []

    # Run all validation checks
    all_errors.extend(validate_required_fields(entry, schema))
    all_errors.extend(validate_field_types(entry, schema))
    all_errors.extend(validate_enum_values(entry, schema))
    all_errors.extend(validate_ranges(entry, schema))
    all_errors.extend(validate_uuid_format(entry))

    return len(all_errors) == 0, all_errors


def validate_file(file_path: Path, schema: Dict[str, Any]) -> Tuple[int, int, List[str]]:
    """
    Validate a JSON file containing misconfiguration entries

    Returns:
        Tuple of (total_entries, valid_entries, errors)
    """
    data = load_json_file(file_path)

    # Handle different file structures
    if 'misconfigurations' in data:
        entries = data['misconfigurations']
    elif isinstance(data, list):
        entries = data
    else:
        entries = [data]

    total_entries = len(entries)
    valid_entries = 0
    all_errors = []

    for idx, entry in enumerate(entries):
        is_valid, errors = validate_entry(entry, schema)

        if is_valid:
            valid_entries += 1
        else:
            entry_id = entry.get('id', f'entry-{idx}')
            all_errors.append(f"\nEntry {entry_id}:")
            for error in errors:
                all_errors.append(f"  - {error}")

    return total_entries, valid_entries, all_errors


def main():
    parser = argparse.ArgumentParser(
        description="Validate AWS misconfiguration JSON files against schema"
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="Path(s) to JSON files or directories to validate"
    )
    parser.add_argument(
        "--schema",
        default="schema/misconfig-schema.json",
        help="Path to JSON schema file (default: schema/misconfig-schema.json)"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with error if any validation fails"
    )

    args = parser.parse_args()

    # Load schema
    schema_path = Path(args.schema)
    if not schema_path.exists():
        print(f"Error: Schema file not found: {schema_path}")
        return 1

    print(f"Loading schema from: {schema_path}")
    schema = load_schema(schema_path)
    print()

    # Collect all JSON files to validate
    json_files = []
    for path_str in args.paths:
        path = Path(path_str)
        if path.is_file():
            if path.suffix == '.json':
                json_files.append(path)
        elif path.is_dir():
            json_files.extend(path.rglob('*.json'))
        else:
            print(f"Warning: Path not found: {path}")

    if not json_files:
        print("No JSON files found to validate")
        return 1

    print(f"Found {len(json_files)} JSON file(s) to validate")
    print("=" * 60)
    print()

    # Validate each file
    total_files = len(json_files)
    valid_files = 0
    total_entries = 0
    total_valid_entries = 0
    has_errors = False

    for json_file in sorted(json_files):
        print(f"Validating: {json_file}")

        try:
            entries, valid, errors = validate_file(json_file, schema)
            total_entries += entries
            total_valid_entries += valid

            if errors:
                has_errors = True
                print(f"  ✗ {valid}/{entries} entries valid")
                for error in errors:
                    print(f"    {error}")
            else:
                valid_files += 1
                print(f"  ✓ All {entries} entries valid")

        except json.JSONDecodeError as e:
            has_errors = True
            print(f"  ✗ JSON parsing error: {e}")
        except Exception as e:
            has_errors = True
            print(f"  ✗ Validation error: {e}")

        print()

    # Print summary
    print("=" * 60)
    print("Validation Summary")
    print("=" * 60)
    print(f"Files validated: {valid_files}/{total_files}")
    print(f"Entries validated: {total_valid_entries}/{total_entries}")

    if has_errors:
        print()
        print("⚠️  Validation completed with errors")
        if args.strict:
            return 1
        return 0
    else:
        print()
        print("✓ All validations passed!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
