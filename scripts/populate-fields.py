#!/usr/bin/env python3
"""
Populate missing fields in AWS Misconfiguration recommendations.
Fills: alert_criteria, recommendation_action, effort_level, risk_value, action_value
"""

import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data" / "by-service"


def derive_alert_criteria(entry):
    """Derive alert_criteria from scenario and description."""
    scenario = entry.get('scenario', '')
    description = entry.get('recommendation_description_detailed', '')
    risk = entry.get('risk_detail', '')

    # Common patterns for alert criteria
    scenario_lower = scenario.lower()

    # Idle/unused resources
    if any(word in scenario_lower for word in ['idle', 'unused', 'unattached', 'orphan']):
        if 'ebs' in scenario_lower or 'volume' in scenario_lower:
            return "EBS volume has been unattached for more than 7 days"
        if 'elastic ip' in scenario_lower or 'eip' in scenario_lower:
            return "Elastic IP is not associated with any running instance"
        if 'load balancer' in scenario_lower or 'elb' in scenario_lower or 'alb' in scenario_lower:
            return "Load balancer has received less than 100 requests in the past 7 days"
        if 'ec2' in scenario_lower or 'instance' in scenario_lower:
            return "EC2 instance CPU utilization has been below 5% for the past 14 days"
        if 'nat' in scenario_lower:
            return "NAT Gateway has processed less than 1GB of data in the past 30 days"
        if 'rds' in scenario_lower or 'database' in scenario_lower:
            return "RDS instance has had zero connections for the past 7 days"
        return f"Resource has been idle or unused for an extended period"

    # Security-related
    if 'security' in risk:
        if 'encrypt' in scenario_lower:
            return "Resource is not encrypted or uses outdated encryption"
        if 'public' in scenario_lower:
            return "Resource is publicly accessible when it should not be"
        if 'password' in scenario_lower or 'credential' in scenario_lower:
            return "Credentials are not rotated within the recommended period"
        if 'iam' in scenario_lower or 'permission' in scenario_lower or 'policy' in scenario_lower:
            return "IAM policy grants excessive permissions or violates least privilege"
        if 'logging' in scenario_lower or 'audit' in scenario_lower:
            return "Logging or auditing is not enabled for this resource"
        if 'ssl' in scenario_lower or 'tls' in scenario_lower or 'https' in scenario_lower:
            return "Resource is not using secure transport (TLS/SSL)"
        return "Security configuration does not meet best practices"

    # Cost-related
    if 'cost' in risk:
        if 'reserved' in scenario_lower or 'savings' in scenario_lower:
            return "On-demand usage exceeds 30% of total compute hours"
        if 'rightsiz' in scenario_lower or 'oversiz' in scenario_lower:
            return "Resource is consistently underutilized (CPU/memory below 40%)"
        if 'generation' in scenario_lower or 'previous' in scenario_lower:
            return "Resource is using a previous generation instance type"
        if 'storage' in scenario_lower:
            return "Storage tier does not match access patterns"
        return "Resource cost could be optimized"

    # Performance-related
    if 'performance' in risk:
        if 'throttl' in scenario_lower:
            return "Resource is experiencing throttling events"
        if 'latency' in scenario_lower:
            return "Latency exceeds acceptable thresholds"
        if 'capacity' in scenario_lower:
            return "Resource is approaching capacity limits"
        if 'cache' in scenario_lower:
            return "Cache hit ratio is below optimal threshold"
        return "Performance metrics indicate optimization opportunity"

    # Reliability-related
    if 'reliability' in risk:
        if 'backup' in scenario_lower:
            return "Automated backups are not configured"
        if 'replica' in scenario_lower or 'multi-az' in scenario_lower:
            return "High availability configuration is not enabled"
        if 'failover' in scenario_lower:
            return "Failover mechanism is not properly configured"
        return "Reliability configuration does not meet best practices"

    # Operations-related (default)
    if 'tag' in scenario_lower:
        return "Resource is missing required tags"
    if 'monitor' in scenario_lower:
        return "Monitoring is not properly configured"
    if 'alarm' in scenario_lower:
        return "CloudWatch alarms are not configured"
    if 'config' in scenario_lower or 'setting' in scenario_lower:
        return "Configuration does not follow recommended settings"

    # Fallback based on scenario
    return f"Condition detected: {scenario[:100]}"


def derive_recommendation_action(entry):
    """Derive recommendation_action from scenario and description."""
    scenario = entry.get('scenario', '')
    description = entry.get('recommendation_description_detailed', '')
    risk = entry.get('risk_detail', '')

    scenario_lower = scenario.lower()

    # Idle/unused resources
    if any(word in scenario_lower for word in ['idle', 'unused', 'unattached', 'orphan']):
        return "Review resource usage and delete if no longer needed, or investigate why it's idle"

    # Security-related
    if 'security' in risk:
        if 'encrypt' in scenario_lower:
            return "Enable encryption using AWS KMS or service-managed keys"
        if 'public' in scenario_lower:
            return "Restrict public access and implement proper access controls"
        if 'password' in scenario_lower or 'credential' in scenario_lower:
            return "Implement credential rotation policy and enable automatic rotation"
        if 'iam' in scenario_lower or 'permission' in scenario_lower:
            return "Review and restrict IAM permissions following least privilege principle"
        if 'logging' in scenario_lower:
            return "Enable logging and configure log retention policies"
        return "Review and update security configuration to meet best practices"

    # Cost-related
    if 'cost' in risk:
        if 'reserved' in scenario_lower or 'savings' in scenario_lower:
            return "Analyze usage patterns and purchase Reserved Instances or Savings Plans"
        if 'rightsiz' in scenario_lower or 'oversiz' in scenario_lower:
            return "Right-size the resource based on actual utilization metrics"
        if 'generation' in scenario_lower:
            return "Migrate to current generation instance type for better price-performance"
        if 'storage' in scenario_lower:
            return "Review storage tier and implement lifecycle policies"
        return "Review resource configuration for cost optimization opportunities"

    # Performance-related
    if 'performance' in risk:
        if 'throttl' in scenario_lower:
            return "Increase provisioned capacity or implement request queuing"
        if 'cache' in scenario_lower:
            return "Review cache configuration and implement caching strategy"
        return "Optimize resource configuration for improved performance"

    # Reliability-related
    if 'reliability' in risk:
        if 'backup' in scenario_lower:
            return "Enable automated backups and configure retention period"
        if 'replica' in scenario_lower or 'multi-az' in scenario_lower:
            return "Enable Multi-AZ deployment or read replicas for high availability"
        return "Implement redundancy and failover mechanisms"

    # Operations defaults
    if 'tag' in scenario_lower:
        return "Apply required tags following organizational tagging strategy"
    if 'monitor' in scenario_lower:
        return "Configure CloudWatch monitoring and create dashboards"

    return "Review and update configuration following AWS best practices"


def derive_numeric_values(entry):
    """Derive effort_level, risk_value, and action_value from entry data."""
    risk_detail = entry.get('risk_detail', 'operations')
    build_priority = entry.get('build_priority')
    scenario = entry.get('scenario', '').lower()

    # Default values
    effort = 2  # Medium effort
    risk = 2    # Medium risk
    value = 2   # Medium value

    # Adjust based on risk_detail
    if 'security' in risk_detail:
        risk = 3  # Security issues are higher risk
        value = 3  # High value to fix
    elif 'cost' in risk_detail:
        risk = 1  # Cost issues are lower risk
        value = 3  # High value (direct savings)
    elif 'reliability' in risk_detail:
        risk = 3  # Reliability issues are high risk
        value = 3  # High value
    elif 'performance' in risk_detail:
        risk = 2  # Medium risk
        value = 2  # Medium value

    # Adjust based on build_priority
    if build_priority is not None:
        if build_priority == 0:  # Critical
            value = 3
            risk = 3
        elif build_priority == 1:  # High
            value = 2
            risk = 2
        elif build_priority >= 2:  # Medium/Low
            value = 1
            risk = 1

    # Adjust effort based on scenario complexity
    if any(word in scenario for word in ['migration', 'refactor', 'architecture', 'redesign']):
        effort = 3  # High effort
    elif any(word in scenario for word in ['enable', 'configure', 'tag', 'update']):
        effort = 1  # Low effort
    elif any(word in scenario for word in ['delete', 'remove', 'disable']):
        effort = 1  # Low effort

    return effort, risk, value


def process_file(filepath):
    """Process a single JSON file and populate missing fields."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if 'misconfigurations' not in data:
        return 0

    updated = 0
    for entry in data['misconfigurations']:
        modified = False

        # Check and fill alert_criteria
        if not entry.get('alert_criteria') or not entry['alert_criteria'].strip():
            entry['alert_criteria'] = derive_alert_criteria(entry)
            modified = True

        # Check and fill recommendation_action
        if not entry.get('recommendation_action') or not entry['recommendation_action'].strip():
            entry['recommendation_action'] = derive_recommendation_action(entry)
            modified = True

        # Check and fill numeric values
        if entry.get('effort_level') is None or entry.get('risk_value') is None or entry.get('action_value') is None:
            effort, risk, value = derive_numeric_values(entry)
            if entry.get('effort_level') is None:
                entry['effort_level'] = effort
                modified = True
            if entry.get('risk_value') is None:
                entry['risk_value'] = risk
                modified = True
            if entry.get('action_value') is None:
                entry['action_value'] = value
                modified = True

        if modified:
            updated += 1

    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return updated


def main():
    print("Populating missing fields in recommendations...\n")

    total_updated = 0
    for json_file in sorted(DATA_DIR.glob("*.json")):
        updated = process_file(json_file)
        if updated > 0:
            print(f"  {json_file.name}: {updated} entries updated")
            total_updated += updated

    print(f"\nTotal: {total_updated} entries updated")
    print("\nRun 'python3 scripts/db-init.py' to rebuild the database")


if __name__ == "__main__":
    main()
