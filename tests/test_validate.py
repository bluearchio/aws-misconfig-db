"""Tests for scripts/validate.py — the schema validation script."""

import json
import sys
from pathlib import Path

import pytest

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.validate import (
    load_schema,
    load_json_file,
    validate_required_fields,
    validate_field_types,
    validate_enum_values,
    validate_ranges,
    validate_uuid_format,
    validate_entry,
    validate_file,
)


class TestLoadSchema:
    def test_loads_real_schema(self):
        """Load actual schema from schema/misconfig-schema.json."""
        schema_path = PROJECT_ROOT / "schema" / "misconfig-schema.json"
        schema = load_schema(schema_path)
        assert "properties" in schema
        assert "required" in schema
        assert "id" in schema["properties"]
        assert "service_name" in schema["properties"]

    def test_missing_file_raises(self, tmp_path):
        """Loading a non-existent schema file should raise an error."""
        with pytest.raises(FileNotFoundError):
            load_schema(tmp_path / "nonexistent.json")


class TestLoadJsonFile:
    def test_loads_valid_json(self, tmp_path):
        """Load a valid JSON file."""
        data = {"key": "value", "count": 42}
        filepath = tmp_path / "test.json"
        filepath.write_text(json.dumps(data))
        result = load_json_file(filepath)
        assert result == data

    def test_missing_file_raises(self, tmp_path):
        """Loading a non-existent JSON file should raise an error."""
        with pytest.raises(FileNotFoundError):
            load_json_file(tmp_path / "missing.json")

    def test_invalid_json_raises(self, tmp_path):
        """Loading invalid JSON should raise a decode error."""
        filepath = tmp_path / "bad.json"
        filepath.write_text("{invalid json}")
        with pytest.raises(json.JSONDecodeError):
            load_json_file(filepath)


class TestValidateRequiredFields:
    def test_all_required_present(self, mock_schema, sample_recommendation):
        """No errors when all required fields are present."""
        errors = validate_required_fields(sample_recommendation, mock_schema)
        assert errors == []

    def test_missing_id(self, mock_schema, sample_recommendation):
        """Error when 'id' field is missing."""
        del sample_recommendation["id"]
        errors = validate_required_fields(sample_recommendation, mock_schema)
        assert any("id" in e for e in errors)

    def test_missing_service_name(self, mock_schema, sample_recommendation):
        """Error when 'service_name' field is missing."""
        del sample_recommendation["service_name"]
        errors = validate_required_fields(sample_recommendation, mock_schema)
        assert any("service_name" in e for e in errors)

    def test_empty_string_field(self, mock_schema, sample_recommendation):
        """Empty string for a required field should be flagged."""
        sample_recommendation["scenario"] = ""
        errors = validate_required_fields(sample_recommendation, mock_schema)
        assert any("scenario" in e for e in errors)

    def test_none_field(self, mock_schema, sample_recommendation):
        """None value for a required field should be flagged."""
        sample_recommendation["risk_detail"] = None
        errors = validate_required_fields(sample_recommendation, mock_schema)
        assert any("risk_detail" in e for e in errors)


class TestValidateFieldTypes:
    def test_valid_types(self, mock_schema, sample_recommendation):
        """No errors when all field types are correct."""
        errors = validate_field_types(sample_recommendation, mock_schema)
        assert errors == []

    def test_wrong_type_string_for_int(self, mock_schema, sample_recommendation):
        """Error when a string is provided where an integer is expected."""
        sample_recommendation["build_priority"] = "high"
        errors = validate_field_types(sample_recommendation, mock_schema)
        assert any("build_priority" in e for e in errors)

    def test_nullable_fields(self, mock_schema, sample_recommendation):
        """Nullable fields (like action_value) should accept None without error."""
        sample_recommendation["action_value"] = None
        errors = validate_field_types(sample_recommendation, mock_schema)
        assert not any("action_value" in e for e in errors)

    def test_wrong_type_int_for_string(self, mock_schema, sample_recommendation):
        """Error when an integer is provided where a string is expected."""
        sample_recommendation["scenario"] = 12345
        errors = validate_field_types(sample_recommendation, mock_schema)
        assert any("scenario" in e for e in errors)

    def test_array_field_valid(self, mock_schema, sample_recommendation):
        """Array fields should validate correctly."""
        sample_recommendation["tags"] = ["tag1", "tag2"]
        errors = validate_field_types(sample_recommendation, mock_schema)
        assert not any("tags" in e for e in errors)

    def test_array_field_wrong_type(self, mock_schema, sample_recommendation):
        """Error when a non-array value is given for an array field."""
        sample_recommendation["tags"] = "not-an-array"
        errors = validate_field_types(sample_recommendation, mock_schema)
        assert any("tags" in e for e in errors)


class TestValidateEnumValues:
    def test_valid_enum(self, mock_schema, sample_recommendation):
        """No errors for valid enum values."""
        errors = validate_enum_values(sample_recommendation, mock_schema)
        assert errors == []

    def test_invalid_enum_value(self, mock_schema, sample_recommendation):
        """Error when a field has an invalid enum value."""
        # The schema uses pattern for risk_detail, not enum.
        # architectural_patterns items have enum for 'relationship'.
        # We test by adding an enum field to the schema for the test.
        schema_with_enum = json.loads(json.dumps(mock_schema))
        schema_with_enum["properties"]["category"] = {
            "type": "string",
            "enum": ["compute", "networking", "database", "storage", "security"],
        }
        sample_recommendation["category"] = "invalid_category"
        errors = validate_enum_values(sample_recommendation, schema_with_enum)
        assert any("category" in e for e in errors)

    def test_none_value_skipped(self, mock_schema, sample_recommendation):
        """None values should not trigger enum validation."""
        schema_with_enum = json.loads(json.dumps(mock_schema))
        schema_with_enum["properties"]["category"] = {
            "type": "string",
            "enum": ["compute", "networking", "storage"],
        }
        sample_recommendation["category"] = None
        errors = validate_enum_values(sample_recommendation, schema_with_enum)
        assert not any("category" in e for e in errors)


class TestValidateRanges:
    def test_valid_ranges(self, mock_schema, sample_recommendation):
        """No errors when all values are within range."""
        errors = validate_ranges(sample_recommendation, mock_schema)
        assert errors == []

    def test_priority_below_min(self, mock_schema, sample_recommendation):
        """Error when build_priority is below minimum (0)."""
        sample_recommendation["build_priority"] = -1
        errors = validate_ranges(sample_recommendation, mock_schema)
        assert any("build_priority" in e and "below minimum" in e for e in errors)

    def test_priority_above_max(self, mock_schema, sample_recommendation):
        """Error when build_priority exceeds maximum (3)."""
        sample_recommendation["build_priority"] = 4
        errors = validate_ranges(sample_recommendation, mock_schema)
        assert any("build_priority" in e and "exceeds maximum" in e for e in errors)

    def test_effort_level_max(self, mock_schema, sample_recommendation):
        """effort_level at maximum (3) should be valid."""
        sample_recommendation["effort_level"] = 3
        errors = validate_ranges(sample_recommendation, mock_schema)
        assert not any("effort_level" in e for e in errors)

    def test_effort_level_above_max(self, mock_schema, sample_recommendation):
        """Error when effort_level exceeds maximum (3)."""
        sample_recommendation["effort_level"] = 5
        errors = validate_ranges(sample_recommendation, mock_schema)
        assert any("effort_level" in e and "exceeds maximum" in e for e in errors)

    def test_risk_value_at_min(self, mock_schema, sample_recommendation):
        """risk_value at minimum (0) should be valid."""
        sample_recommendation["risk_value"] = 0
        errors = validate_ranges(sample_recommendation, mock_schema)
        assert not any("risk_value" in e for e in errors)

    def test_none_value_skipped(self, mock_schema, sample_recommendation):
        """None values should not trigger range validation."""
        sample_recommendation["action_value"] = None
        errors = validate_ranges(sample_recommendation, mock_schema)
        assert not any("action_value" in e for e in errors)


class TestValidateUuidFormat:
    def test_valid_uuid(self):
        """Valid lowercase UUID should pass."""
        entry = {"id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"}
        errors = validate_uuid_format(entry)
        assert errors == []

    def test_invalid_uuid(self):
        """Invalid UUID format should produce an error."""
        entry = {"id": "not-a-uuid"}
        errors = validate_uuid_format(entry)
        assert len(errors) == 1
        assert "UUID" in errors[0]

    def test_uppercase_uuid(self):
        """Uppercase UUID should be rejected (schema requires lowercase)."""
        entry = {"id": "A1B2C3D4-E5F6-7890-ABCD-EF1234567890"}
        errors = validate_uuid_format(entry)
        assert len(errors) == 1

    def test_no_id_field(self):
        """Entry without 'id' field should produce no errors from UUID check."""
        entry = {"service_name": "s3"}
        errors = validate_uuid_format(entry)
        assert errors == []

    def test_valid_uuid_v4(self):
        """Standard UUID v4 format should pass."""
        entry = {"id": "e9b21a0d-2fe8-4f5b-8875-52995b4cf2e7"}
        errors = validate_uuid_format(entry)
        assert errors == []


class TestValidateEntry:
    def test_valid_entry(self, mock_schema, sample_recommendation):
        """A fully valid entry should pass all checks."""
        is_valid, errors = validate_entry(sample_recommendation, mock_schema)
        assert is_valid
        assert errors == []

    def test_invalid_entry_missing_required(self, mock_schema):
        """An entry missing required fields should fail."""
        incomplete = {"scenario": "test"}
        is_valid, errors = validate_entry(incomplete, mock_schema)
        assert not is_valid
        assert len(errors) > 0

    def test_invalid_entry_bad_uuid(self, mock_schema, sample_recommendation):
        """An entry with an invalid UUID should fail."""
        sample_recommendation["id"] = "BAD-UUID"
        is_valid, errors = validate_entry(sample_recommendation, mock_schema)
        assert not is_valid
        assert any("UUID" in e for e in errors)

    def test_invalid_entry_bad_range(self, mock_schema, sample_recommendation):
        """An entry with an out-of-range value should fail."""
        sample_recommendation["build_priority"] = 99
        is_valid, errors = validate_entry(sample_recommendation, mock_schema)
        assert not is_valid


class TestValidateFile:
    def test_valid_service_file(self, mock_schema, tmp_data_dir):
        """Validate the s3.json file from tmp_data_dir fixture."""
        s3_file = tmp_data_dir / "by-service" / "s3.json"
        total, valid, errors = validate_file(s3_file, mock_schema)
        assert total == 2
        assert valid == 2
        assert errors == []

    def test_invalid_entries(self, mock_schema, tmp_path):
        """File with invalid entries should report errors."""
        data = {
            "service": "test",
            "count": 1,
            "misconfigurations": [
                {
                    "id": "INVALID-UUID",
                    "service_name": "test",
                    "scenario": "test scenario",
                    "risk_detail": "security",
                    "build_priority": 99,
                }
            ],
        }
        filepath = tmp_path / "invalid.json"
        filepath.write_text(json.dumps(data))

        total, valid, errors = validate_file(filepath, mock_schema)
        assert total == 1
        assert valid == 0
        assert len(errors) > 0

    def test_list_format(self, mock_schema, tmp_path):
        """Validate a file that contains a plain JSON list of entries."""
        entries = [
            {
                "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "service_name": "ec2",
                "scenario": "EC2 instance without termination protection",
                "risk_detail": "reliability",
                "build_priority": 1,
                "action_value": 2,
                "effort_level": 1,
                "risk_value": 2,
                "recommendation_description_detailed": "Enable termination protection.",
                "category": "compute",
                "references": [],
                "tags": [],
            }
        ]
        filepath = tmp_path / "list_format.json"
        filepath.write_text(json.dumps(entries))

        total, valid, errors = validate_file(filepath, mock_schema)
        assert total == 1
        assert valid == 1

    def test_empty_misconfigurations(self, mock_schema, tmp_path):
        """File with empty misconfigurations list should report zero entries."""
        data = {"service": "empty", "count": 0, "misconfigurations": []}
        filepath = tmp_path / "empty.json"
        filepath.write_text(json.dumps(data))

        total, valid, errors = validate_file(filepath, mock_schema)
        assert total == 0
        assert valid == 0
        assert errors == []
