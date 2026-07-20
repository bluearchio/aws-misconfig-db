#!/usr/bin/env python3
"""Generate the BlueArch website Governance Hub catalog from aws-misconfig-db."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_DIR = PROJECT_ROOT / "data" / "by-service"
DEFAULT_OUTPUT = (
    PROJECT_ROOT.parent
    / "bluearch-website"
    / "frontend"
    / "app"
    / "src"
    / "data"
    / "governanceCatalog.json"
)


def _severity(value: Any) -> str:
    try:
        risk = int(value)
    except (TypeError, ValueError):
        return "Medium"
    if risk >= 3:
        return "High"
    if risk == 2:
        return "Medium"
    return "Low"


def _risk_types(value: Any) -> list[str]:
    if not value:
        return []
    return [part.strip().lower() for part in str(value).split(",") if part.strip()]


def _entry_to_finding(entry: dict[str, Any]) -> dict[str, Any]:
    service = str(entry.get("service_name") or "").strip().lower()
    title = str(entry.get("scenario") or entry.get("recommendation_action") or entry.get("id")).strip()
    risk_types = _risk_types(entry.get("risk_detail"))
    metadata = entry.get("metadata") if isinstance(entry.get("metadata"), dict) else {}

    return {
        "id": entry.get("id"),
        "title": title,
        "service": service,
        "serviceLabel": service.upper() if service else "AWS",
        "severity": _severity(entry.get("risk_value")),
        "riskTypes": risk_types,
        "riskDetail": entry.get("risk_detail") or "",
        "category": entry.get("category") or "",
        "alertCriteria": entry.get("alert_criteria") or "",
        "recommendation": entry.get("recommendation_action") or "",
        "description": entry.get("recommendation_description_detailed") or "",
        "outputNotes": entry.get("output_notes") or "",
        "notes": entry.get("notes") or "",
        "references": entry.get("references") if isinstance(entry.get("references"), list) else [],
        "buildPriority": entry.get("build_priority"),
        "actionValue": entry.get("action_value"),
        "effortLevel": entry.get("effort_level"),
        "riskValue": entry.get("risk_value"),
        "updatedAt": metadata.get("updated_at") or metadata.get("created_at") or "",
        "source": metadata.get("source") or "",
        "contributors": metadata.get("contributors") if isinstance(metadata.get("contributors"), list) else [],
        "tags": entry.get("tags") if isinstance(entry.get("tags"), list) else [],
    }


def build_catalog(source_dir: Path) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []

    for path in sorted(source_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for entry in data.get("misconfigurations", []):
            finding = _entry_to_finding(entry)
            if finding["id"]:
                findings.append(finding)

    findings.sort(key=lambda item: (item["service"], item["title"].lower(), item["id"]))

    service_counts: dict[str, int] = {}
    severity_counts: dict[str, int] = {}
    risk_counts: dict[str, int] = {}
    for finding in findings:
        service_counts[finding["service"]] = service_counts.get(finding["service"], 0) + 1
        severity_counts[finding["severity"]] = severity_counts.get(finding["severity"], 0) + 1
        for risk in finding["riskTypes"]:
            risk_counts[risk] = risk_counts.get(risk, 0) + 1

    services = [
        {
            "service": service,
            "label": service.upper(),
            "count": count,
        }
        for service, count in sorted(service_counts.items(), key=lambda item: (-item[1], item[0]))
    ]

    return {
        "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "aws-misconfig-db/data/by-service",
        "total": len(findings),
        "services": services,
        "severityCounts": severity_counts,
        "riskCounts": dict(sorted(risk_counts.items())),
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    if not args.source_dir.exists():
        parser.error(f"source directory does not exist: {args.source_dir}")

    catalog = build_catalog(args.source_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Synced {catalog['total']} Governance Hub findings to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
