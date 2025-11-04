#!/usr/bin/env python3
"""
Basic Usage Example for AWS Misconfiguration Database

This script demonstrates how to load and query the database.
"""

import json
from pathlib import Path
from typing import List, Dict, Any


def load_database(file_path: str = "../../data/all-misconfigs.json") -> Dict[str, Any]:
    """Load the complete misconfiguration database"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_service_data(service: str, data_dir: str = "../../data/by-service") -> Dict[str, Any]:
    """Load misconfigurations for a specific AWS service"""
    service_file = Path(data_dir) / f"{service}.json"
    with open(service_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def filter_by_risk(misconfigs: List[Dict], risk_type: str) -> List[Dict]:
    """Filter misconfigurations by risk type"""
    return [
        m for m in misconfigs
        if risk_type in m.get('risk_detail', '')
    ]


def filter_by_priority(misconfigs: List[Dict], max_priority: int = 1) -> List[Dict]:
    """Filter misconfigurations by priority (0 = highest)"""
    return [
        m for m in misconfigs
        if m.get('build_priority') is not None and m.get('build_priority') <= max_priority
    ]


def filter_by_service(misconfigs: List[Dict], service: str) -> List[Dict]:
    """Filter misconfigurations by AWS service"""
    return [
        m for m in misconfigs
        if m.get('service_name') == service
    ]


def search_scenarios(misconfigs: List[Dict], keyword: str) -> List[Dict]:
    """Search for keyword in scenario descriptions"""
    keyword_lower = keyword.lower()
    return [
        m for m in misconfigs
        if keyword_lower in m.get('scenario', '').lower()
        or keyword_lower in m.get('recommendation_description_detailed', '').lower()
    ]


def get_cost_optimizations(misconfigs: List[Dict], min_value: int = 2) -> List[Dict]:
    """Get cost optimization opportunities sorted by value"""
    cost_items = filter_by_risk(misconfigs, 'cost')
    high_value = [
        m for m in cost_items
        if m.get('action_value') is not None and m.get('action_value') >= min_value
    ]
    return sorted(high_value, key=lambda x: (x.get('effort_level', 99), -x.get('action_value', 0)))


def get_security_critical(misconfigs: List[Dict]) -> List[Dict]:
    """Get critical security misconfigurations"""
    security_items = filter_by_risk(misconfigs, 'security')
    return [
        m for m in security_items
        if m.get('risk_value', 0) >= 2  # Medium to high risk
    ]


def print_misconfiguration(misconfig: Dict, detailed: bool = False):
    """Pretty print a misconfiguration entry"""
    print(f"\nID: {misconfig.get('id')}")
    print(f"Service: {misconfig.get('service_name')}")
    print(f"Scenario: {misconfig.get('scenario')}")
    print(f"Risk: {misconfig.get('risk_detail')} (Priority: {misconfig.get('build_priority')})")
    print(f"Recommendation: {misconfig.get('recommendation_action')}")

    if detailed:
        if misconfig.get('alert_criteria'):
            print(f"\nAlert Criteria: {misconfig.get('alert_criteria')}")
        if misconfig.get('recommendation_description_detailed'):
            print(f"\nDetailed Description: {misconfig.get('recommendation_description_detailed')}")
        if misconfig.get('references'):
            print("\nReferences:")
            for ref in misconfig.get('references', []):
                print(f"  - {ref}")


def main():
    # Example 1: Load and explore the database
    print("=" * 60)
    print("Example 1: Load Database")
    print("=" * 60)

    db = load_database()
    print(f"Total misconfigurations: {db['total_count']}")
    print(f"Services covered: {len(db['services'])}")
    print(f"Categories: {', '.join(db['categories'])}")

    # Example 2: Filter by risk type
    print("\n" + "=" * 60)
    print("Example 2: Security Misconfigurations")
    print("=" * 60)

    security_issues = filter_by_risk(db['misconfigurations'], 'security')
    print(f"Found {len(security_issues)} security-related misconfigurations")

    for misconfig in security_issues[:3]:
        print_misconfiguration(misconfig)

    # Example 3: High-priority items
    print("\n" + "=" * 60)
    print("Example 3: High Priority Issues")
    print("=" * 60)

    high_priority = filter_by_priority(db['misconfigurations'], max_priority=0)
    print(f"Found {len(high_priority)} critical priority misconfigurations")

    # Example 4: Cost optimizations
    print("\n" + "=" * 60)
    print("Example 4: Best Cost Optimizations (High Value, Low Effort)")
    print("=" * 60)

    cost_opts = get_cost_optimizations(db['misconfigurations'], min_value=2)
    print(f"Found {len(cost_opts)} high-value cost optimizations")

    for misconfig in cost_opts[:5]:
        effort = misconfig.get('effort_level', '?')
        value = misconfig.get('action_value', '?')
        print(f"\n- {misconfig.get('scenario')} (Effort: {effort}, Value: {value})")
        print(f"  Recommendation: {misconfig.get('recommendation_action')}")

    # Example 5: Service-specific query
    print("\n" + "=" * 60)
    print("Example 5: EC2-Specific Misconfigurations")
    print("=" * 60)

    ec2_data = load_service_data('ec2')
    print(f"Found {ec2_data['count']} EC2 misconfigurations")

    # Example 6: Search by keyword
    print("\n" + "=" * 60)
    print("Example 6: Search for 'encryption'")
    print("=" * 60)

    encryption_items = search_scenarios(db['misconfigurations'], 'encryption')
    print(f"Found {len(encryption_items)} items related to encryption")

    for misconfig in encryption_items[:3]:
        print(f"\n- {misconfig.get('service_name')}: {misconfig.get('scenario')}")


if __name__ == "__main__":
    main()
