"""Tests for LLM conversion module."""

import json
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.ingest.convert import (
    LLMConverter,
    derive_alert_criteria,
    derive_recommendation_action,
    derive_numeric_values,
)
from scripts.ingest import RawItem


class TestDeriveAlertCriteria:
    def test_idle_resource(self):
        result = derive_alert_criteria({"scenario": "Idle EC2 instance detected", "risk_detail": "cost"})
        assert "idle" in result.lower() or "unused" in result.lower()

    def test_security_encryption(self):
        result = derive_alert_criteria({"scenario": "S3 encryption not enabled", "risk_detail": "security"})
        assert "encrypt" in result.lower()

    def test_security_public(self):
        result = derive_alert_criteria({"scenario": "Public S3 bucket", "risk_detail": "security"})
        assert "public" in result.lower()

    def test_cost_rightsizing(self):
        result = derive_alert_criteria({"scenario": "Oversized EC2 instance", "risk_detail": "cost"})
        assert "underutilized" in result.lower() or "cost" in result.lower()

    def test_fallback(self):
        result = derive_alert_criteria({"scenario": "Something unusual", "risk_detail": "operations"})
        assert len(result) > 0


class TestDeriveRecommendationAction:
    def test_idle_resource(self):
        result = derive_recommendation_action({"scenario": "Unused EBS volume", "risk_detail": "cost"})
        assert "review" in result.lower() or "delete" in result.lower()

    def test_security(self):
        result = derive_recommendation_action({"scenario": "Encryption disabled", "risk_detail": "security"})
        assert len(result) > 0


class TestDeriveNumericValues:
    def test_security_risk(self):
        effort, risk, value = derive_numeric_values({"risk_detail": "security", "scenario": "test"})
        assert risk == 3
        assert value == 3

    def test_cost_risk(self):
        effort, risk, value = derive_numeric_values({"risk_detail": "cost", "scenario": "test"})
        assert risk == 1
        assert value == 3

    def test_low_effort_enable(self):
        effort, risk, value = derive_numeric_values({"risk_detail": "operations", "scenario": "enable logging"})
        assert effort == 1

    def test_high_effort_migration(self):
        effort, risk, value = derive_numeric_values({"risk_detail": "operations", "scenario": "migration to new architecture"})
        assert effort == 3


class TestLLMConverter:
    def test_no_api_key_raises(self):
        converter = LLMConverter(api_key=None)
        with patch.dict("os.environ", {}, clear=True):
            # Remove any ANTHROPIC_API_KEY from env
            import os
            old = os.environ.pop("ANTHROPIC_API_KEY", None)
            try:
                with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
                    converter._get_client()
            finally:
                if old:
                    os.environ["ANTHROPIC_API_KEY"] = old

    @patch("scripts.ingest.convert.LLMConverter._get_client")
    def test_convert_success(self, mock_get_client, sample_raw_item, sample_recommendation):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(sample_recommendation))]
        mock_client.messages.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        converter = LLMConverter(api_key="test-key")
        converter.client = mock_client
        result = converter.convert(sample_raw_item)

        assert result is not None
        assert result["service_name"] == "s3"

    @patch("scripts.ingest.convert.LLMConverter._get_client")
    def test_convert_skip_signal(self, mock_get_client, sample_raw_item):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"skip": true, "reason": "Not an AWS misconfiguration"}')]
        mock_client.messages.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        converter = LLMConverter(api_key="test-key")
        converter.client = mock_client
        result = converter.convert(sample_raw_item)

        assert result is None

    def test_backfill_fills_missing(self):
        converter = LLMConverter(api_key="test-key")
        entry = {
            "id": "",
            "service_name": "s3",
            "scenario": "test encryption",
            "risk_detail": "security",
        }
        result = converter._backfill(entry)

        assert result["id"]  # Should have UUID
        assert result["alert_criteria"]
        assert result["recommendation_action"]
        assert result["effort_level"] is not None
        assert result["risk_value"] is not None
        assert result["action_value"] is not None
        assert "metadata" in result

    def test_backfill_preserves_existing(self):
        converter = LLMConverter(api_key="test-key")
        entry = {
            "id": "existing-id",
            "service_name": "s3",
            "scenario": "test",
            "risk_detail": "security",
            "alert_criteria": "Custom criteria",
            "effort_level": 1,
            "risk_value": 2,
            "action_value": 3,
        }
        result = converter._backfill(entry)

        assert result["id"] == "existing-id"
        assert result["alert_criteria"] == "Custom criteria"
        assert result["effort_level"] == 1
