#!/usr/bin/env python3
"""
AWS Scanner Example using Misconfiguration Database

This script demonstrates how to use the database to scan actual AWS resources
for misconfigurations using boto3.

Prerequisites:
    pip install boto3

Usage:
    python aws_scanner.py --profile my-aws-profile --region us-east-1
"""

import json
import boto3
from typing import List, Dict, Any
import argparse


def load_database(file_path: str = "../../data/all-misconfigs.json") -> Dict[str, Any]:
    """Load the misconfiguration database"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def check_unencrypted_ebs_volumes(ec2_client, misconfig_db: List[Dict]) -> List[Dict]:
    """
    Check for unencrypted EBS volumes

    Relates to misconfig: "user has unencrypted volumes currently in use"
    """
    findings = []

    # Find the relevant misconfiguration
    rule = next(
        (m for m in misconfig_db if 'unencrypted volumes' in m.get('scenario', '').lower()),
        None
    )

    if not rule:
        print("Warning: No rule found for unencrypted volumes")
        return findings

    # Scan for unencrypted volumes
    try:
        response = ec2_client.describe_volumes()

        for volume in response['Volumes']:
            if not volume.get('Encrypted', False):
                findings.append({
                    'rule_id': rule['id'],
                    'service': 'ec2',
                    'resource_type': 'EBS Volume',
                    'resource_id': volume['VolumeId'],
                    'risk_type': rule.get('risk_detail'),
                    'severity': rule.get('risk_value', 1),
                    'scenario': rule.get('scenario'),
                    'recommendation': rule.get('recommendation_action'),
                    'details': {
                        'volume_id': volume['VolumeId'],
                        'size': volume['Size'],
                        'state': volume['State'],
                        'encrypted': volume.get('Encrypted', False)
                    }
                })

    except Exception as e:
        print(f"Error checking EBS volumes: {e}")

    return findings


def check_idle_ec2_instances(ec2_client, cloudwatch_client, misconfig_db: List[Dict]) -> List[Dict]:
    """
    Check for idle/underutilized EC2 instances

    Relates to misconfig: "user has instances that are not being used regularly"
    """
    findings = []

    rule = next(
        (m for m in misconfig_db if 'not being used regularly' in m.get('scenario', '').lower()),
        None
    )

    if not rule:
        return findings

    try:
        response = ec2_client.describe_instances(
            Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
        )

        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_id = instance['InstanceId']

                # Check CPU utilization (simplified - would need more robust checking in production)
                # This is a demonstration of how you'd integrate the database with actual checks

                findings.append({
                    'rule_id': rule['id'],
                    'service': 'ec2',
                    'resource_type': 'EC2 Instance',
                    'resource_id': instance_id,
                    'risk_type': rule.get('risk_detail'),
                    'severity': rule.get('risk_value', 1),
                    'scenario': rule.get('scenario'),
                    'recommendation': rule.get('recommendation_action'),
                    'details': {
                        'instance_id': instance_id,
                        'instance_type': instance['InstanceType'],
                        'state': instance['State']['Name'],
                        'note': 'Further monitoring required to confirm low utilization'
                    }
                })

    except Exception as e:
        print(f"Error checking EC2 instances: {e}")

    return findings


def check_unattached_eip(ec2_client, misconfig_db: List[Dict]) -> List[Dict]:
    """
    Check for unattached Elastic IP addresses

    Relates to misconfig: "Unassociated Elastic IP Addresses"
    """
    findings = []

    rule = next(
        (m for m in misconfig_db if 'Elastic IP' in m.get('scenario', '')),
        None
    )

    if not rule:
        return findings

    try:
        response = ec2_client.describe_addresses()

        for address in response['Addresses']:
            if 'AssociationId' not in address:
                findings.append({
                    'rule_id': rule['id'],
                    'service': 'ec2',
                    'resource_type': 'Elastic IP',
                    'resource_id': address.get('PublicIp'),
                    'risk_type': rule.get('risk_detail'),
                    'severity': rule.get('risk_value', 1),
                    'scenario': rule.get('scenario'),
                    'recommendation': rule.get('recommendation_action'),
                    'details': {
                        'public_ip': address.get('PublicIp'),
                        'allocation_id': address.get('AllocationId'),
                        'domain': address.get('Domain')
                    }
                })

    except Exception as e:
        print(f"Error checking Elastic IPs: {e}")

    return findings


def check_old_iam_keys(iam_client, misconfig_db: List[Dict], max_age_days: int = 90) -> List[Dict]:
    """
    Check for IAM access keys older than threshold

    Relates to misconfig: "IAM key is older than 90 days"
    """
    findings = []

    rule = next(
        (m for m in misconfig_db if 'IAM key' in m.get('scenario', '') and '90 days' in m.get('scenario', '')),
        None
    )

    if not rule:
        return findings

    try:
        from datetime import datetime, timezone

        # Get credential report
        response = iam_client.list_users()

        for user in response['Users']:
            username = user['UserName']

            # Get access keys for user
            keys_response = iam_client.list_access_keys(UserName=username)

            for key in keys_response['AccessKeyMetadata']:
                create_date = key['CreateDate']
                age_days = (datetime.now(timezone.utc) - create_date).days

                if age_days > max_age_days:
                    findings.append({
                        'rule_id': rule['id'],
                        'service': 'iam',
                        'resource_type': 'IAM Access Key',
                        'resource_id': key['AccessKeyId'],
                        'risk_type': rule.get('risk_detail'),
                        'severity': rule.get('risk_value', 2),
                        'scenario': rule.get('scenario'),
                        'recommendation': rule.get('recommendation_action'),
                        'details': {
                            'username': username,
                            'access_key_id': key['AccessKeyId'],
                            'age_days': age_days,
                            'status': key['Status'],
                            'created_date': create_date.isoformat()
                        }
                    })

    except Exception as e:
        print(f"Error checking IAM keys: {e}")

    return findings


def generate_report(findings: List[Dict], output_file: str = None):
    """Generate a report of findings"""

    print("\n" + "=" * 60)
    print("AWS Misconfiguration Scan Report")
    print("=" * 60)

    if not findings:
        print("\n✓ No misconfigurations found!")
        return

    # Group by risk type
    by_risk = {}
    for finding in findings:
        risk = finding.get('risk_type', 'unknown')
        by_risk.setdefault(risk, []).append(finding)

    print(f"\nTotal Findings: {len(findings)}")
    print(f"\nBreakdown by Risk Type:")
    for risk, items in sorted(by_risk.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  {risk}: {len(items)}")

    print("\n" + "=" * 60)
    print("Detailed Findings")
    print("=" * 60)

    for idx, finding in enumerate(findings, 1):
        print(f"\n[{idx}] {finding['resource_type']}: {finding['resource_id']}")
        print(f"    Service: {finding['service']}")
        print(f"    Risk: {finding['risk_type']} (Severity: {finding['severity']})")
        print(f"    Issue: {finding['scenario']}")
        print(f"    Recommendation: {finding['recommendation']}")

        if finding.get('details'):
            print(f"    Details:")
            for key, value in finding['details'].items():
                print(f"      - {key}: {value}")

    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'scan_date': datetime.now(timezone.utc).isoformat(),
                'total_findings': len(findings),
                'findings': findings
            }, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Full report saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Scan AWS infrastructure for misconfigurations"
    )
    parser.add_argument('--profile', help='AWS profile to use')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--output', help='Output file for report (JSON)')
    parser.add_argument('--db-path', default='../../data/all-misconfigs.json',
                        help='Path to misconfiguration database')

    args = parser.parse_args()

    # Setup AWS session
    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    ec2_client = session.client('ec2')
    iam_client = session.client('iam')
    cloudwatch_client = session.client('cloudwatch')

    print(f"Loading misconfiguration database from: {args.db_path}")
    db = load_database(args.db_path)
    misconfigs = db['misconfigurations']

    print(f"Loaded {len(misconfigs)} misconfiguration rules")
    print(f"Scanning AWS account in region: {args.region}")
    print()

    all_findings = []

    # Run checks
    print("Checking for unencrypted EBS volumes...")
    all_findings.extend(check_unencrypted_ebs_volumes(ec2_client, misconfigs))

    print("Checking for unattached Elastic IPs...")
    all_findings.extend(check_unattached_eip(ec2_client, misconfigs))

    print("Checking for old IAM access keys...")
    all_findings.extend(check_old_iam_keys(iam_client, misconfigs))

    # Generate report
    generate_report(all_findings, args.output)


if __name__ == "__main__":
    from datetime import datetime, timezone
    main()
