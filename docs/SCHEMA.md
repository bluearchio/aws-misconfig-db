# AWS Misconfiguration Database Schema

This document provides detailed documentation for the AWS Misconfiguration Database JSON schema.

## Schema Version

Current version: 1.0.0

The schema follows [JSON Schema Draft 07](http://json-schema.org/draft-07/schema#) specification.

## Entry Structure

Each misconfiguration entry in the database follows this structure:

```json
{
  "id": "string (UUID)",
  "status": "enum",
  "service_name": "string",
  "scenario": "string",
  "alert_criteria": "string",
  "recommendation_action": "string",
  "risk_detail": "enum",
  "build_priority": "integer (0-3)",
  "action_value": "integer or null",
  "effort_level": "integer (0-3) or null",
  "risk_value": "integer (0-3) or null",
  "recommendation_description_detailed": "string",
  "category": "string",
  "output_notes": "string",
  "notes": "string",
  "references": ["array of URLs"],
  "metadata": {
    "created_at": "ISO 8601 datetime",
    "updated_at": "ISO 8601 datetime",
    "contributors": ["array of strings"],
    "source": "string"
  },
  "tags": ["array of strings"],
  "cve_references": ["array of CVE IDs"],
  "compliance_mappings": ["array of strings"],
  "detection_methods": [
    {
      "method": "string",
      "details": "string"
    }
  ],
  "remediation_examples": [
    {
      "language": "string",
      "code": "string",
      "description": "string"
    }
  ]
}
```

## Field Definitions

### Required Fields

#### `id` (string, required)
- **Type**: String
- **Format**: UUID v4
- **Pattern**: `^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$`
- **Description**: Unique identifier for the misconfiguration entry
- **Example**: `"550e8400-e29b-41d4-a716-446655440000"`

Generate UUIDs:
```python
import uuid
str(uuid.uuid4())
```

#### `service_name` (string, required)
- **Type**: String
- **Description**: AWS service affected by this misconfiguration
- **Format**: Lowercase, use hyphens for multi-word services
- **Examples**:
  - `"ec2"`
  - `"s3"`
  - `"rds"`
  - `"alb-elb"`
  - `"route-53"`

Common service names:
- Compute: `ec2`, `lambda`, `ecs`, `eks`, `elastic-beanstalk`
- Storage: `s3`, `ebs`, `efs`
- Database: `rds`, `dynamodb`, `redshift`, `elasticache`
- Networking: `vpc`, `cloudfront`, `route-53`, `alb-elb`
- Security: `iam`, `kms`, `secrets-manager`
- Operations: `cloudwatch`, `cloudtrail`, `config`

#### `scenario` (string, required)
- **Type**: String
- **Description**: Brief description of the misconfiguration scenario
- **Guidelines**:
  - Keep to 1-2 sentences
  - Be specific about what's wrong
  - Focus on the "what" not the "why" (use detailed description for that)
- **Example**: `"EC2 instances are running on previous generation instance types"`

#### `risk_detail` (string, required)
- **Type**: String (enum)
- **Allowed Values**:
  - `"cost"` - Cost optimization opportunity
  - `"security"` - Security vulnerability or best practice
  - `"operations"` - Operational efficiency or management
  - `"performance"` - Performance improvement
  - `"reliability"` - Reliability or availability concern
  - Multiple values separated by comma: `"cost, operations"`
- **Description**: Type(s) of risk associated with this misconfiguration
- **Example**: `"cost"`

### Optional Core Fields

#### `status` (string, optional)
- **Type**: String (enum)
- **Default**: `"open"`
- **Allowed Values**:
  - `"done"` - Entry is complete and validated
  - `"ice"` - On hold, needs more information or discussion
  - `"open"` - New entry, awaiting validation
  - `"pending"` - Being actively worked on
- **Description**: Current status of the misconfiguration entry

#### `alert_criteria` (string, optional)
- **Type**: String
- **Description**: Specific conditions or metrics that trigger this alert
- **Guidelines**:
  - Be measurable and specific
  - Include thresholds where applicable
  - Use metrics that can be programmatically checked
- **Examples**:
  - `"CPU utilization < 5% for 4+ days in last 14 days"`
  - `"EBS volume is unencrypted"`
  - `"IAM key has not been rotated in 90+ days"`

#### `recommendation_action` (string, optional)
- **Type**: String
- **Description**: Recommended action to remediate the misconfiguration
- **Guidelines**:
  - Start with an action verb
  - Be clear and specific
  - Provide actionable steps
- **Examples**:
  - `"Upgrade to current generation instance types (t3, m5, c5)"`
  - `"Enable encryption on EBS volumes"`
  - `"Rotate IAM access keys"`

#### `build_priority` (integer, optional)
- **Type**: Integer
- **Range**: 0-3
- **Description**: Priority level for addressing this misconfiguration
  - `0` - Critical/Highest priority
  - `1` - High priority
  - `2` - Medium priority
  - `3` - Low priority
- **Note**: Lower numbers = higher priority

#### `action_value` (integer or null, optional)
- **Type**: Integer or null
- **Range**: Typically 1-3
- **Description**: Estimated value or impact of implementing the recommendation
  - `1` - Low value/impact
  - `2` - Medium value/impact
  - `3` - High value/impact

#### `effort_level` (integer or null, optional)
- **Type**: Integer or null
- **Range**: 0-3
- **Description**: Estimated effort required to implement the recommendation
  - `0` - Minimal effort
  - `1` - Low effort
  - `2` - Medium effort
  - `3` - High effort

#### `risk_value` (integer or null, optional)
- **Type**: Integer or null
- **Range**: 0-3
- **Description**: Severity of the risk if not addressed
  - `0` - Minimal risk
  - `1` - Low risk
  - `2` - Medium risk
  - `3` - High/Critical risk

#### `recommendation_description_detailed` (string, optional)
- **Type**: String
- **Description**: Comprehensive explanation of the recommendation and its benefits
- **Guidelines**:
  - Explain why this matters
  - Describe the impact of not fixing
  - Provide context
  - Include technical details
  - Be comprehensive but concise

#### `category` (string, optional)
- **Type**: String
- **Description**: Category of AWS resource or service type
- **Common Values**:
  - `"compute"` - Compute resources (EC2, Lambda, etc.)
  - `"networking"` - Networking services
  - `"database"` - Database services
  - `"storage"` - Storage services
  - `"security"` - Security services

#### `output_notes` (string, optional)
- **Type**: String
- **Description**: Additional output notes, pros and cons
- **Usage**: Supplementary information about tradeoffs or considerations

#### `notes` (string, optional)
- **Type**: String
- **Description**: Additional notes or context about the misconfiguration
- **Usage**: Internal notes, special considerations, caveats

### Reference Fields

#### `references` (array, optional)
- **Type**: Array of strings
- **Format**: Each string must be a valid URL (HTTPS preferred)
- **Max Items**: 10
- **Description**: Reference URLs for documentation and resources
- **Examples**:
```json
"references": [
  "https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-encryption.html",
  "https://aws.amazon.com/blogs/security/encrypt-ebs-volumes/"
]
```

### Metadata

#### `metadata` (object, optional)
- **Type**: Object
- **Description**: Metadata about the entry

##### `metadata.created_at` (string)
- **Format**: ISO 8601 datetime
- **Example**: `"2025-01-04T10:30:00Z"`

##### `metadata.updated_at` (string)
- **Format**: ISO 8601 datetime
- **Example**: `"2025-01-04T10:30:00Z"`

##### `metadata.contributors` (array)
- **Type**: Array of strings
- **Description**: GitHub usernames of contributors
- **Example**: `["username1", "username2"]`

##### `metadata.source` (string)
- **Description**: Original source of the misconfiguration entry
- **Examples**:
  - `"AWS Trusted Advisor"`
  - `"AWS Well-Architected Framework"`
  - `"Community Contribution"`
  - `"CIS Benchmark"`

### Extended Fields

#### `tags` (array, optional)
- **Type**: Array of strings
- **Description**: Searchable tags for categorization
- **Guidelines**: Use lowercase, hyphen-separated tags
- **Examples**: `["encryption", "data-protection", "compliance"]`

#### `cve_references` (array, optional)
- **Type**: Array of strings
- **Format**: CVE identifier format `CVE-YYYY-NNNN`
- **Description**: Related CVE identifiers if applicable
- **Example**: `["CVE-2021-12345"]`

#### `compliance_mappings` (array, optional)
- **Type**: Array of strings
- **Description**: Compliance frameworks this relates to
- **Common Values**:
  - `"PCI-DSS"`
  - `"HIPAA"`
  - `"SOC2"`
  - `"CIS"`
  - `"NIST"`
  - `"ISO-27001"`

#### `detection_methods` (array, optional)
- **Type**: Array of objects
- **Description**: Methods to detect this misconfiguration

Each detection method object:
```json
{
  "method": "AWS Config Rule",
  "details": "encrypted-volumes"
}
```

**Method types**:
- `"AWS Config Rule"` - AWS Config rule name
- `"CloudWatch Metric"` - CloudWatch metric and threshold
- `"CLI Command"` - AWS CLI command to detect
- `"API Call"` - AWS API call and parameters
- `"Custom Script"` - Custom detection script

#### `remediation_examples` (array, optional)
- **Type**: Array of objects
- **Description**: Code examples for remediation

Each remediation example object:
```json
{
  "language": "python",
  "code": "import boto3\n...",
  "description": "Python script to enable encryption"
}
```

**Language types**:
- `"python"` - Python (boto3)
- `"bash"` - Bash script
- `"terraform"` - Terraform HCL
- `"cloudformation"` - CloudFormation YAML/JSON
- `"aws-cli"` - AWS CLI commands

## Validation

All entries are validated against the schema using `scripts/validate.py`:

```bash
python3 scripts/validate.py data/by-service/
```

Validation checks:
- Required fields are present
- Field types match schema
- Enum values are valid
- UUID format is correct
- URL format is valid
- Integer ranges are respected

## Example Entry

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "done",
  "service_name": "ec2",
  "scenario": "EC2 instances with unencrypted EBS volumes",
  "alert_criteria": "EBS volumes attached to instances have Encrypted=false",
  "recommendation_action": "Enable encryption on all EBS volumes",
  "risk_detail": "security",
  "build_priority": 0,
  "action_value": 3,
  "effort_level": 1,
  "risk_value": 3,
  "recommendation_description_detailed": "Unencrypted EBS volumes pose a security risk as data at rest is not protected. Encryption should be enabled to protect sensitive data and meet compliance requirements. AWS uses KMS keys to encrypt volumes with minimal performance impact.",
  "category": "compute",
  "notes": "Encryption cannot be enabled on existing volumes; must create encrypted snapshot and restore",
  "references": [
    "https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EBSEncryption.html"
  ],
  "metadata": {
    "created_at": "2025-01-04T00:00:00Z",
    "updated_at": "2025-01-04T00:00:00Z",
    "contributors": ["initial-import"],
    "source": "AWS Trusted Advisor"
  },
  "tags": ["encryption", "ebs", "data-protection"],
  "compliance_mappings": ["PCI-DSS", "HIPAA"],
  "detection_methods": [
    {
      "method": "AWS Config Rule",
      "details": "encrypted-volumes"
    },
    {
      "method": "CLI Command",
      "details": "aws ec2 describe-volumes --filters Name=encrypted,Values=false"
    }
  ],
  "remediation_examples": [
    {
      "language": "aws-cli",
      "code": "aws ec2 create-volume --encrypted --kms-key-id arn:aws:kms:region:account:key/key-id",
      "description": "Create an encrypted EBS volume with specified KMS key"
    }
  ]
}
```

## Schema File

The complete JSON Schema is available at: [schema/misconfig-schema.json](../schema/misconfig-schema.json)

## Questions?

If you have questions about the schema, please:
- Open a [Discussion](https://github.com/aws-misconfig-db/aws-misconfig-db/discussions)
- Open an [Issue](https://github.com/aws-misconfig-db/aws-misconfig-db/issues)
