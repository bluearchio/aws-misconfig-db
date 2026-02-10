"""LLM conversion: RawItem -> recommendation dict via Claude API."""

from __future__ import annotations

import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# Rate limiting
MAX_REQUESTS_PER_MINUTE = 20
RETRY_DELAYS = [1, 2, 4]  # Exponential backoff
MAX_RETRIES = 3

# Load schema for the system prompt
SCHEMA_PATH = _project_root / "schema" / "misconfig-schema.json"


def _load_schema_text() -> str:
    """Load schema as text for the LLM prompt."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --- Derivation functions copied from populate-fields.py ---
# (Avoiding fragile import of hyphenated filename)

def derive_alert_criteria(entry):
    """Derive alert_criteria from scenario and description."""
    scenario = entry.get('scenario', '')
    risk = entry.get('risk_detail', '')
    scenario_lower = scenario.lower()

    if any(word in scenario_lower for word in ['idle', 'unused', 'unattached', 'orphan']):
        return "Resource has been idle or unused for an extended period"
    if 'security' in risk:
        if 'encrypt' in scenario_lower:
            return "Resource is not encrypted or uses outdated encryption"
        if 'public' in scenario_lower:
            return "Resource is publicly accessible when it should not be"
        if 'iam' in scenario_lower or 'permission' in scenario_lower:
            return "IAM policy grants excessive permissions or violates least privilege"
        if 'logging' in scenario_lower:
            return "Logging or auditing is not enabled for this resource"
        return "Security configuration does not meet best practices"
    if 'cost' in risk:
        if 'rightsiz' in scenario_lower or 'oversiz' in scenario_lower:
            return "Resource is consistently underutilized (CPU/memory below 40%)"
        return "Resource cost could be optimized"
    if 'performance' in risk:
        return "Performance metrics indicate optimization opportunity"
    if 'reliability' in risk:
        if 'backup' in scenario_lower:
            return "Automated backups are not configured"
        return "Reliability configuration does not meet best practices"
    return f"Condition detected: {scenario[:100]}"


def derive_recommendation_action(entry):
    """Derive recommendation_action from scenario and description."""
    scenario = entry.get('scenario', '')
    risk = entry.get('risk_detail', '')
    scenario_lower = scenario.lower()

    if any(word in scenario_lower for word in ['idle', 'unused', 'unattached', 'orphan']):
        return "Review resource usage and delete if no longer needed, or investigate why it's idle"
    if 'security' in risk:
        if 'encrypt' in scenario_lower:
            return "Enable encryption using AWS KMS or service-managed keys"
        if 'public' in scenario_lower:
            return "Restrict public access and implement proper access controls"
        return "Review and update security configuration to meet best practices"
    if 'cost' in risk:
        return "Review resource configuration for cost optimization opportunities"
    if 'performance' in risk:
        return "Optimize resource configuration for improved performance"
    if 'reliability' in risk:
        return "Implement redundancy and failover mechanisms"
    return "Review and update configuration following AWS best practices"


def derive_numeric_values(entry):
    """Derive effort_level, risk_value, and action_value from entry data."""
    risk_detail = entry.get('risk_detail', 'operations')
    build_priority = entry.get('build_priority')
    scenario = entry.get('scenario', '').lower()

    effort = 2
    risk = 2
    value = 2

    if 'security' in risk_detail:
        risk, value = 3, 3
    elif 'cost' in risk_detail:
        risk, value = 1, 3
    elif 'reliability' in risk_detail:
        risk, value = 3, 3
    elif 'performance' in risk_detail:
        risk, value = 2, 2

    if build_priority is not None:
        if build_priority == 0:
            value, risk = 3, 3
        elif build_priority == 1:
            value, risk = 2, 2
        elif build_priority >= 2:
            value, risk = 1, 1

    if any(word in scenario for word in ['migration', 'refactor', 'architecture', 'redesign']):
        effort = 3
    elif any(word in scenario for word in ['enable', 'configure', 'tag', 'update', 'delete', 'remove', 'disable']):
        effort = 1

    return effort, risk, value


# --- End derivation functions ---


SYSTEM_PROMPT_TEMPLATE = """You are an expert AWS cloud architect. Convert the following source material into a structured AWS misconfiguration recommendation.

Output ONLY valid JSON matching this schema:
{schema}

IMPORTANT RULES:
1. "id" must be a new UUID v4
2. "service_name" must be a lowercase AWS service identifier (e.g., "ec2", "s3", "iam", "rds", "lambda")
3. "scenario" should describe the misconfiguration scenario concisely
4. "risk_detail" must match the pattern: one or more of (cost, security, operations, performance, reliability) separated by ", "
5. "build_priority" should be 0 (critical), 1 (high), 2 (medium), or 3 (low)
6. All text fields should be clear, professional, and actionable
7. If the source material is not about an AWS misconfiguration or best practice, output {{"skip": true, "reason": "Not an AWS misconfiguration recommendation"}}
8. If relevant, include "estimated_cost_impact" with an approximate cost range (e.g., "$10-50/month per resource")
9. If relevant, include "compliance_frameworks" as an array of framework identifiers (e.g., ["CIS", "SOC2", "HIPAA", "PCI-DSS"])
10. If relevant, include "aws_doc_url" with the canonical AWS documentation link

Example output:
{{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "service_name": "s3",
  "scenario": "S3 bucket does not have server-side encryption enabled",
  "alert_criteria": "S3 bucket default encryption is not configured",
  "recommendation_action": "Enable default encryption on the S3 bucket using SSE-S3 or SSE-KMS",
  "risk_detail": "security",
  "build_priority": 0,
  "action_value": 3,
  "effort_level": 1,
  "risk_value": 3,
  "recommendation_description_detailed": "S3 buckets should have default encryption enabled to protect data at rest. Without encryption, data stored in S3 is vulnerable to unauthorized access if bucket permissions are misconfigured.",
  "category": "storage",
  "references": ["https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucket-encryption.html"],
  "metadata": {{
    "created_at": "{now}",
    "updated_at": "{now}",
    "contributors": ["ingest-pipeline"],
    "source": "{source_name}"
  }},
  "tags": ["encryption", "s3", "data-protection"],
  "estimated_cost_impact": "$0 - minimal cost for enabling encryption",
  "compliance_frameworks": ["CIS", "SOC2", "HIPAA", "PCI-DSS", "NIST-800-53"],
  "aws_doc_url": "https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucket-encryption.html"
}}"""


class LLMConverter:
    """Converts RawItems to recommendation dicts using Claude API."""

    def __init__(self, model: str = "claude-sonnet-4-20250514", api_key: str | None = None):
        self.model = model
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.client = None
        self._request_times: list[float] = []
        self._schema_text = _load_schema_text()

    def _get_client(self):
        """Lazy-init the Anthropic client."""
        if self.client is None:
            if not self.api_key:
                raise RuntimeError("ANTHROPIC_API_KEY not set. Use --skip-llm or set the environment variable.")
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
        return self.client

    def _rate_limit(self):
        """Enforce rate limiting (MAX_REQUESTS_PER_MINUTE)."""
        now = time.time()
        # Remove timestamps older than 60 seconds
        self._request_times = [t for t in self._request_times if now - t < 60]
        if len(self._request_times) >= MAX_REQUESTS_PER_MINUTE:
            sleep_time = 60 - (now - self._request_times[0])
            if sleep_time > 0:
                logger.info("Rate limiting: sleeping %.1fs", sleep_time)
                time.sleep(sleep_time)
        self._request_times.append(time.time())

    def convert(self, raw_item) -> dict[str, Any] | None:
        """
        Convert a RawItem to a recommendation dict.

        Returns:
            Recommendation dict, or None if skipped/failed.
        """
        now = _now_iso()

        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            schema=self._schema_text,
            now=now,
            source_name=raw_item.source_name,
        )

        user_prompt = f"""Source: {raw_item.source_name}
Title: {raw_item.title}
URL: {raw_item.url}
Categories: {', '.join(raw_item.categories)}

Content:
{raw_item.body[:4000]}"""

        for attempt in range(MAX_RETRIES):
            try:
                self._rate_limit()
                client = self._get_client()

                response = client.messages.create(
                    model=self.model,
                    max_tokens=2000,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                )

                text = response.content[0].text.strip()

                # Extract JSON from response (handle markdown code blocks)
                if text.startswith("```"):
                    lines = text.split("\n")
                    text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])

                result = json.loads(text)

                # Check for skip signal
                if result.get("skip"):
                    logger.info("LLM skipped item: %s - %s", raw_item.title, result.get("reason", ""))
                    return None

                # Backfill any empty optional fields
                result = self._backfill(result)

                return result

            except json.JSONDecodeError as e:
                if attempt < MAX_RETRIES - 1:
                    logger.warning("Invalid JSON from LLM (attempt %d), retrying with repair prompt", attempt + 1)
                    user_prompt = f"Your previous response was not valid JSON. Error: {e}\nPlease output ONLY valid JSON.\n\n{user_prompt}"
                    time.sleep(RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)])
                else:
                    logger.error("Failed to get valid JSON after %d attempts for: %s", MAX_RETRIES, raw_item.title)
                    return None

            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "rate" in error_str.lower():
                    delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
                    logger.warning("Rate limited, backing off %ds", delay)
                    time.sleep(delay)
                elif attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
                    logger.warning("LLM error (attempt %d): %s, retrying in %ds", attempt + 1, e, delay)
                    time.sleep(delay)
                else:
                    logger.error("LLM conversion failed after %d attempts: %s", MAX_RETRIES, e)
                    return None

        return None

    def _backfill(self, entry: dict) -> dict:
        """Backfill empty optional fields using derivation functions."""
        # Ensure ID is valid UUID
        if not entry.get("id"):
            entry["id"] = str(uuid.uuid4())

        # Backfill alert_criteria
        if not entry.get("alert_criteria"):
            entry["alert_criteria"] = derive_alert_criteria(entry)

        # Backfill recommendation_action
        if not entry.get("recommendation_action"):
            entry["recommendation_action"] = derive_recommendation_action(entry)

        # Backfill numeric values
        if entry.get("effort_level") is None or entry.get("risk_value") is None or entry.get("action_value") is None:
            effort, risk, value = derive_numeric_values(entry)
            if entry.get("effort_level") is None:
                entry["effort_level"] = effort
            if entry.get("risk_value") is None:
                entry["risk_value"] = risk
            if entry.get("action_value") is None:
                entry["action_value"] = value

        # Ensure metadata exists
        if "metadata" not in entry:
            entry["metadata"] = {}
        now = _now_iso()
        entry["metadata"].setdefault("created_at", now)
        entry["metadata"].setdefault("updated_at", now)
        entry["metadata"].setdefault("contributors", ["ingest-pipeline"])

        # Default empty arrays
        entry.setdefault("references", [])
        entry.setdefault("tags", [])

        return entry
