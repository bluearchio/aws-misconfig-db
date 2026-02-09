"""GitHub repository rule file parser."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from scripts.ingest import RawItem
from scripts.ingest.parsers import BaseParser

logger = logging.getLogger(__name__)


class GitHubParser(BaseParser):
    """Parses rule definition files from GitHub repositories."""

    def parse(self, raw_content: Any) -> list[RawItem]:
        """Parse GitHub file contents into RawItems."""
        if raw_content is None:
            return []

        items = []
        for file_info in raw_content:
            try:
                file_items = self._parse_file(file_info)
                items.extend(file_items)
            except Exception as e:
                logger.warning("Failed to parse %s: %s", file_info.get("path", ""), e)

        logger.info("Source %s: parsed %d items from %d files", self.source_id, len(items), len(raw_content))
        return items

    def _parse_file(self, file_info: dict) -> list[RawItem]:
        """Parse a single rule file."""
        path = file_info["path"]
        content = file_info["content"]
        url = file_info["url"]

        if path.endswith(".py"):
            return self._parse_python_check(path, content, url)
        elif path.endswith((".yaml", ".yml")):
            return self._parse_yaml_rule(path, content, url)
        elif path.endswith(".json"):
            return self._parse_json_rule(path, content, url)
        else:
            return self._parse_generic(path, content, url)

    def _parse_python_check(self, path: str, content: str, url: str) -> list[RawItem]:
        """Parse Python check files (e.g., Prowler, ScoutSuite)."""
        items = []

        # Look for check metadata in class definitions or module docstrings
        # Prowler pattern: class CheckName with CheckMetadata
        class_match = re.search(
            r'class\s+(\w+)\s*\(.*?\):\s*"""(.*?)"""',
            content,
            re.DOTALL,
        )

        # Try to find check name/description from common patterns
        check_id_match = re.search(r'(?:CheckID|check_id|name)\s*=\s*["\']([^"\']+)["\']', content)
        desc_match = re.search(r'(?:Description|description|desc)\s*=\s*["\']([^"\']+)["\']', content)
        severity_match = re.search(r'(?:Severity|severity|risk)\s*=\s*["\']([^"\']+)["\']', content)
        service_match = re.search(r'(?:ServiceName|service_name|service)\s*=\s*["\']([^"\']+)["\']', content)

        title = ""
        body = ""

        if check_id_match:
            title = check_id_match.group(1)
        elif class_match:
            title = class_match.group(1)
            body = class_match.group(2).strip()
        else:
            # Extract from filename
            raw_filename = path.split("/")[-1].replace(".py", "")
            if raw_filename in ("__init__", "models", "lib", "utils", "common"):
                return []
            title = raw_filename.replace("_", " ")

        if desc_match and not body:
            body = desc_match.group(1)

        if not body:
            # Use docstring or first comment block
            docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
            if docstring_match:
                body = docstring_match.group(1).strip()

        if not body:
            body = f"Security check from {path}"

        metadata = {}
        if severity_match:
            metadata["severity"] = severity_match.group(1)
        if service_match:
            metadata["service"] = service_match.group(1)

        items.append(RawItem(
            source_id=self.source_id,
            source_name=self.source_name,
            title=title,
            body=body[:4000],
            url=url,
            categories=list(self.categories),
            raw_metadata={**metadata, "file_path": path, "file_type": "python"},
        ))

        return items

    def _parse_yaml_rule(self, path: str, content: str, url: str) -> list[RawItem]:
        """Parse YAML rule files."""
        items = []

        # Simple YAML parsing for rule metadata without importing yaml
        title_match = re.search(r'(?:name|title|id)\s*:\s*(.+)', content)
        desc_match = re.search(r'(?:description|desc|message)\s*:\s*["\']?(.+?)["\']?\s*$', content, re.MULTILINE)
        severity_match = re.search(r'(?:severity|risk|level)\s*:\s*(.+)', content)

        title = title_match.group(1).strip().strip("'\"") if title_match else path.split("/")[-1]
        body = desc_match.group(1).strip() if desc_match else content[:500]

        metadata = {"file_path": path, "file_type": "yaml"}
        if severity_match:
            metadata["severity"] = severity_match.group(1).strip().strip("'\"")

        items.append(RawItem(
            source_id=self.source_id,
            source_name=self.source_name,
            title=title,
            body=body[:4000],
            url=url,
            categories=list(self.categories),
            raw_metadata=metadata,
        ))

        return items

    def _parse_json_rule(self, path: str, content: str, url: str) -> list[RawItem]:
        """Parse JSON rule files."""
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return []

        if isinstance(data, list):
            rules = data
        elif isinstance(data, dict):
            rules = [data]
        else:
            return []

        items = []
        for rule in rules:
            title = rule.get("name") or rule.get("title") or rule.get("id") or ""
            body = rule.get("description") or rule.get("message") or str(rule)

            if title:
                items.append(RawItem(
                    source_id=self.source_id,
                    source_name=self.source_name,
                    title=str(title),
                    body=str(body)[:4000],
                    url=url,
                    categories=list(self.categories),
                    raw_metadata={"file_path": path, "file_type": "json", "rule_data": rule},
                ))

        return items

    def _parse_generic(self, path: str, content: str, url: str) -> list[RawItem]:
        """Parse generic text files as single items."""
        filename = path.split("/")[-1]
        return [RawItem(
            source_id=self.source_id,
            source_name=self.source_name,
            title=filename,
            body=content[:4000],
            url=url,
            categories=list(self.categories),
            raw_metadata={"file_path": path, "file_type": "generic"},
        )]
