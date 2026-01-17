#!/usr/bin/env python3
"""
Classify entries from general.json into appropriate AWS service files.
"""

import json
import os
import re
from pathlib import Path
from datetime import datetime, timezone

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data" / "by-service"

# Classification rules: (service_name, file_name, keywords/patterns)
CLASSIFICATION_RULES = [
    # EC2 related
    ("ec2", "ec2.json", [
        r"\bec2\b", r"\binstance\b", r"\bami\b", r"\bplacement group\b",
        r"\belastic ip\b", r"\beip\b", r"\beni\b", r"\bauto.?scaling\b",
        r"\basg\b", r"\bspot\b", r"\breserved instance\b", r"\bnitro\b",
        r"\bboot time\b", r"\bmulti.?threading\b", r"\bcore count\b",
        r"\bgolden image\b"
    ]),

    # EBS related
    ("ebs", "ebs.json", [
        r"\bebs\b", r"\bvolume\b", r"\biops\b", r"\braid\b",
        r"\bsnapshot\b", r"\broot volume\b", r"\bmulti.?attach\b"
    ]),

    # S3 related
    ("s3", "s3.json", [
        r"\bs3\b(?!\s*bucket)", r"s3 bucket", r"\bbucket\b", r"\bglacier\b",
        r"\bs3ia\b", r"\bpresigned\b", r"\bversioning\b.*s3", r"s3.*versioning",
        r"s3.*encryption", r"s3.*logging", r"s3.*acl", r"s3.*ssl",
        r"s3.*sse", r"s3.*public", r"s3.*replication", r"s3.*crr",
        r"s3.*select", r"s3.*transfer acceleration"
    ]),

    # RDS related
    ("rds", "rds.json", [
        r"\brds\b", r"\baurora\b", r"\bread replica\b", r"\bdatabase\b.*sql",
        r"sql.*database", r"\bserverless v[12]\b", r"\bparameter group\b",
        r"db instance", r"analytics.*rds", r"rds.*analytics"
    ]),

    # DynamoDB related
    ("dynamodb", "dynamodb.json", [
        r"\bdynamodb\b", r"\bdynamo\b", r"\bdax\b", r"\brcu\b",
        r"\bwcu\b", r"\bhot.?key\b", r"\bhot.?shard\b", r"\bglobal table\b",
        r"provisioned.*throughput"
    ]),

    # Lambda related
    ("lambda", "lambda.json", [
        r"\blambda\b(?!.*cloudfront)", r"serverless.*function",
        r"lambda.*admin", r"lambda.*execution role", r"lambda.*ram",
        r"lambda.*invoked"
    ]),

    # CloudFront related
    ("cloudfront", "cloudfront.json", [
        r"\bcloudfront\b", r"\bcdn\b", r"\bedge location\b",
        r"\bsigned url\b.*cloudfront", r"cloudfront.*signed",
        r"\bsigned cookie\b", r"\bgeo restriction\b", r"\btls\b.*cdn",
        r"cdn.*tls", r"origin.*cloudfront"
    ]),

    # ALB/ELB related
    ("alb/elb", "alb-elb.json", [
        r"\belb\b", r"\balb\b", r"\bnlb\b", r"\bload.?balancer\b",
        r"health.?check.*elb", r"elb.*health", r"listener.*certificate",
        r"elb.*ssl", r"ssl.*elb", r"elb.*cipher", r"elb.*access log"
    ]),

    # VPC/Networking related
    ("networking", "networking.json", [
        r"\bvpc\b", r"\bsubnet\b", r"\bnat gateway\b", r"\bnat instance\b",
        r"\bdirect connect\b", r"\bflow log\b", r"\btransit gateway\b",
        r"\bprivate link\b", r"\bvpc peering\b", r"\bvpc endpoint\b",
        r"\bglobal accelerator\b", r"security group.*vpc", r"vpc.*security"
    ]),

    # Security Groups (could be EC2 or networking - prioritize networking)
    ("networking", "networking.json", [
        r"\bsecurity group\b", r"\bingress\b.*0\.0\.0\.0",
        r"\bssh\b.*port", r"\brdp\b.*port", r"default.*security group"
    ]),

    # IAM related
    ("iam", "iam.json", [
        r"\biam\b", r"\brole\b.*aws", r"aws.*role", r"\bmfa\b",
        r"\broot\b.*account", r"\baccess key\b", r"\bpassword policy\b",
        r"\bcredential\b.*report", r"\bleast privilege\b",
        r"inline.?policy", r"\*:\*", r"\biam user\b"
    ]),

    # CloudTrail related
    ("cloudtrail", "cloudtrail.json", [
        r"\bcloudtrail\b", r"\btrail\b.*multi.?region",
        r"multi.?region.*trail", r"trail.*log"
    ]),

    # CloudWatch related
    ("cloudwatch", "cloudwatch.json", [
        r"\bcloudwatch\b(?!.*cloudtrail)", r"\balarm\b.*metric",
        r"metric.*alarm", r"\bcost.?explorer\b"
    ]),

    # EFS related
    ("efs", "efs.json", [
        r"\befs\b", r"\bfile.?system\b.*amazon", r"amazon.*file.?system",
        r"efs.*encrypt"
    ]),

    # ECS related
    ("ecs", "ecs.json", [
        r"\becs\b", r"\bcontainer\b.*aws", r"aws.*container",
        r"\bfargate\b", r"ecs.*encrypt", r"ecs.*cluster"
    ]),

    # Route53 related
    ("route 53", "route-53.json", [
        r"\broute\s*53\b", r"\bdns\b", r"routing.?policy",
        r"\bgeolocation\b.*routing", r"weighted.*routing",
        r"\blatency\b.*routing", r"health.?check.*route"
    ]),

    # Kinesis related
    ("kinesis", "kinesis.json", [
        r"\bkinesis\b", r"\bdata.?stream\b", r"\bfirehose\b",
        r"video.?stream"
    ]),

    # SQS related
    ("sqs", "sqs.json", [
        r"\bsqs\b", r"\bqueue\b.*message", r"message.*queue",
        r"\bvisibility.?timeout\b"
    ]),

    # SNS related
    ("sns", "sns.json", [
        r"\bsns\b", r"\btopic\b.*subscriber", r"subscriber.*topic"
    ]),

    # ElastiCache related
    ("elasticache", "elasticache.json", [
        r"\belasticache\b", r"\bredis\b", r"\bmemcached\b",
        r"\bcache\b.*aws", r"sorted.?set.*redis"
    ]),

    # KMS related
    ("kms", "kms.json", [
        r"\bkms\b", r"\bcmk\b", r"\bencryption.?key\b",
        r"customer.?master.?key", r"key.?rotation"
    ]),

    # Inspector related
    ("inspector", "inspector.json", [
        r"\binspector\b"
    ]),

    # AWS Config related
    ("aws-config", "aws-config.json", [
        r"\baws.?config\b", r"config.*enabled.*region"
    ]),

    # FSx related
    ("fsx", "fsx.json", [
        r"\bfsx\b", r"\bluster\b", r"windows.*file.?share"
    ]),

    # Storage Gateway related
    ("storage-gateway", "storage-gateway.json", [
        r"\bstorage.?gateway\b", r"file.?gateway", r"volume.?gateway",
        r"tape.?gateway"
    ]),

    # Snow family related
    ("snow", "snow.json", [
        r"\bsnow\b", r"\bsnowball\b", r"\bsnowcone\b", r"\bsnowmobile\b"
    ]),

    # API Gateway related
    ("api-gateway", "api-gateway.json", [
        r"\bapi.?gateway\b", r"edge.?optimized.*api",
        r"private.*api.*gateway", r"api.*gateway.*cache"
    ]),

    # ACM (Certificate Manager)
    ("acm", "acm.json", [
        r"\bcertificate\b.*expir", r"ssl.*certificate.*expir",
        r"tls.*certificate.*expir"
    ]),
]

# Keywords that indicate truly cross-service / general recommendations
GENERAL_KEYWORDS = [
    r"savings.?plan", r"\bfinops\b", r"cost.?allocation.?tag",
    r"decommission", r"\bbudget\b", r"cost.?model",
    r"cost.?aware", r"shared.?resource", r"shared.?infrastructure",
    r"managed.?service.*vs", r"cloud.?financial",
    r"organization.?wide", r"cross.?service"
]


def load_json(filepath):
    """Load JSON file."""
    with open(filepath, "r") as f:
        return json.load(f)


def save_json(filepath, data):
    """Save JSON file with formatting."""
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


def classify_entry(entry):
    """
    Classify an entry based on its content.
    Returns (service_name, file_name) or (None, None) if it should stay general.
    """
    # Combine text fields for analysis
    text = " ".join([
        str(entry.get("scenario", "")),
        str(entry.get("alert_criteria", "")),
        str(entry.get("recommendation_action", "")),
        str(entry.get("recommendation_description_detailed", "")),
        str(entry.get("notes", ""))
    ]).lower()

    # First check if it's truly general/cross-service
    for pattern in GENERAL_KEYWORDS:
        if re.search(pattern, text, re.IGNORECASE):
            return None, None

    # Try to classify by service
    for service_name, file_name, patterns in CLASSIFICATION_RULES:
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return service_name, file_name

    return None, None


def main():
    """Main function to classify and redistribute entries."""
    general_file = DATA_DIR / "general.json"

    # Load general.json
    general_data = load_json(general_file)
    entries = general_data.get("misconfigurations", [])

    print(f"Processing {len(entries)} entries from general.json")

    # Track where entries go
    service_entries = {}  # file_name -> list of entries
    remaining_general = []  # entries that stay in general

    for entry in entries:
        service_name, file_name = classify_entry(entry)

        if service_name and file_name:
            # Update the service_name field
            entry["service_name"] = service_name

            # Update metadata
            if "metadata" not in entry:
                entry["metadata"] = {}
            entry["metadata"]["updated_at"] = datetime.now(timezone.utc).isoformat()
            if "contributors" not in entry["metadata"]:
                entry["metadata"]["contributors"] = []
            if "classification-2026" not in entry["metadata"]["contributors"]:
                entry["metadata"]["contributors"].append("classification-2026")

            if file_name not in service_entries:
                service_entries[file_name] = []
            service_entries[file_name].append(entry)
        else:
            remaining_general.append(entry)

    # Summary
    print(f"\nClassification Results:")
    print(f"  Remaining in general: {len(remaining_general)}")
    print(f"\n  Entries to move:")
    for file_name, entries in sorted(service_entries.items()):
        print(f"    {file_name}: {len(entries)} entries")

    # Update existing service files or create new ones
    for file_name, new_entries in service_entries.items():
        file_path = DATA_DIR / file_name

        if file_path.exists():
            # Load existing file
            existing_data = load_json(file_path)
            existing_entries = existing_data.get("misconfigurations", [])

            # Get existing IDs to avoid duplicates
            existing_ids = {e["id"] for e in existing_entries}

            # Add new entries (skip duplicates)
            for entry in new_entries:
                if entry["id"] not in existing_ids:
                    existing_entries.append(entry)

            existing_data["misconfigurations"] = existing_entries
            existing_data["count"] = len(existing_entries)
        else:
            # Create new file
            service_name = new_entries[0]["service_name"] if new_entries else file_name.replace(".json", "")
            existing_data = {
                "service": service_name,
                "count": len(new_entries),
                "misconfigurations": new_entries
            }

        save_json(file_path, existing_data)
        print(f"  Updated {file_name}: {existing_data['count']} total entries")

    # Update general.json with remaining entries
    general_data["misconfigurations"] = remaining_general
    general_data["count"] = len(remaining_general)
    save_json(general_file, general_data)
    print(f"\n  Updated general.json: {len(remaining_general)} entries")

    print("\nDone! Run scripts/generate.py to regenerate aggregated files.")


if __name__ == "__main__":
    main()
