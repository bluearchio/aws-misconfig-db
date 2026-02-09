"""Integration tests for the pipeline orchestrator."""

import json
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.ingest import RawItem
from scripts.ingest.orchestrator import PipelineOrchestrator


class TestPipelineOrchestrator:
    @patch("scripts.ingest.orchestrator.save_state")
    @patch("scripts.ingest.orchestrator.load_state")
    @patch("scripts.ingest.orchestrator.load_sources")
    def test_dry_run(self, mock_load_sources, mock_load_state, mock_save_state, tmp_data_dir, sample_source_config):
        mock_load_sources.return_value = sample_source_config
        mock_load_state.return_value = {"version": "1.0.0", "sources": {}, "runs": []}

        # Mock fetcher and parser
        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = {
            "content": [{"title": "Test", "summary": "Test content " * 20, "link": "https://x"}],
            "etag": None,
            "last_modified": None,
            "not_modified": False,
        }
        mock_parser = MagicMock()
        mock_parser.parse.return_value = [
            RawItem(
                source_id="test-rss-source",
                source_name="Test",
                title="New Lambda best practice",
                body="Lambda functions should have proper timeout configuration " * 5,
                url="https://example.com/lambda",
                categories=["operations"],
            )
        ]

        with patch("scripts.ingest.orchestrator.get_fetcher", return_value=mock_fetcher), \
             patch("scripts.ingest.orchestrator.get_parser", return_value=mock_parser), \
             patch("scripts.generate.load_all_entries") as mock_load:
            mock_load.return_value = []

            orchestrator = PipelineOrchestrator(
                source_ids=["test-rss-source"],
                dry_run=True,
            )
            metrics = orchestrator.run()

        assert metrics["items_fetched"] == 1
        mock_save_state.assert_not_called()

    @patch("scripts.ingest.orchestrator.stage_recommendation")
    @patch("scripts.ingest.orchestrator.validate_recommendation")
    @patch("scripts.ingest.orchestrator.save_state")
    @patch("scripts.ingest.orchestrator.load_state")
    @patch("scripts.ingest.orchestrator.load_sources")
    def test_full_pipeline_with_llm(self, mock_load_sources, mock_load_state, mock_save_state,
                                      mock_validate, mock_stage, sample_source_config, sample_recommendation):
        mock_load_sources.return_value = sample_source_config
        mock_load_state.return_value = {"version": "1.0.0", "sources": {}, "runs": []}
        mock_validate.return_value = (True, [])
        mock_stage.return_value = Path("/tmp/staged.json")

        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = {
            "content": "raw",
            "etag": None,
            "last_modified": None,
            "not_modified": False,
        }
        mock_parser = MagicMock()
        mock_parser.parse.return_value = [
            RawItem(
                source_id="test-rss-source",
                source_name="Test",
                title="Unique new finding about DynamoDB",
                body="DynamoDB tables should use auto-scaling " * 10,
                url="https://example.com/dynamo",
                categories=["operations"],
            )
        ]

        mock_converter = MagicMock()
        mock_converter.convert.return_value = sample_recommendation

        with patch("scripts.ingest.orchestrator.get_fetcher", return_value=mock_fetcher), \
             patch("scripts.ingest.orchestrator.get_parser", return_value=mock_parser), \
             patch("scripts.generate.load_all_entries", return_value=[]):

            orchestrator = PipelineOrchestrator(source_ids=["test-rss-source"])
            orchestrator.converter = mock_converter
            metrics = orchestrator.run()

        assert metrics["items_fetched"] == 1
        assert metrics["items_staged"] == 1
        mock_save_state.assert_called_once()

    @patch("scripts.ingest.orchestrator.save_state")
    @patch("scripts.ingest.orchestrator.load_state")
    @patch("scripts.ingest.orchestrator.load_sources")
    def test_handles_fetch_error(self, mock_load_sources, mock_load_state, mock_save_state, sample_source_config):
        mock_load_sources.return_value = sample_source_config
        mock_load_state.return_value = {"version": "1.0.0", "sources": {}, "runs": []}

        from scripts.ingest.fetchers import FetchError
        mock_fetcher = MagicMock()
        mock_fetcher.fetch.side_effect = FetchError("Connection refused")

        with patch("scripts.ingest.orchestrator.get_fetcher", return_value=mock_fetcher), \
             patch("scripts.generate.load_all_entries", return_value=[]):

            orchestrator = PipelineOrchestrator(
                source_ids=["test-rss-source"],
                skip_llm=True,
            )
            metrics = orchestrator.run()

        assert len(metrics["errors"]) > 0

    @patch("scripts.ingest.orchestrator.save_state")
    @patch("scripts.ingest.orchestrator.load_state")
    def test_no_sources_config(self, mock_load_state, mock_save_state):
        mock_load_state.return_value = {"version": "1.0.0", "sources": {}, "runs": []}

        with patch("scripts.ingest.orchestrator.load_sources", side_effect=FileNotFoundError("No config")):
            orchestrator = PipelineOrchestrator()
            metrics = orchestrator.run()

        assert len(metrics["errors"]) > 0
