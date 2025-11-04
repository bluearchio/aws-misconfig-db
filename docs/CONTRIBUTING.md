# Contributing to AWS Misconfiguration Database

Thank you for your interest in contributing to the AWS Misconfiguration Database! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Adding New Misconfigurations](#adding-new-misconfigurations)
- [Improving Existing Entries](#improving-existing-entries)
- [Submission Process](#submission-process)
- [Style Guidelines](#style-guidelines)
- [Validation](#validation)
- [Review Process](#review-process)

## Code of Conduct

This project adheres to a code of conduct that all contributors are expected to follow. Please be respectful, inclusive, and professional in all interactions.

## How Can I Contribute?

There are many ways to contribute to this project:

1. **Add new misconfiguration entries** - Document new AWS misconfigurations
2. **Improve existing entries** - Add details, references, or remediation steps
3. **Add detection methods** - Provide AWS Config rules or CLI commands
4. **Add remediation examples** - Contribute Terraform, CloudFormation, or script examples
5. **Fix typos or errors** - Improve documentation and correct mistakes
6. **Suggest improvements** - Open issues with suggestions for new features
7. **Review pull requests** - Help review and test contributions from others

## Adding New Misconfigurations

### Step 1: Check for Duplicates

Before adding a new entry, search the existing database to ensure it doesn't already exist:

```bash
# Search by service
grep -r "your-search-term" data/by-service/

# Or check the unified file
cat data/all-misconfigs.json | jq '.misconfigurations[] | select(.scenario | contains("your-search-term"))'
```

### Step 2: Create Your Entry

Create a new JSON entry following the schema. You can use this template:

```json
{
  "id": "generate-uuid-here",
  "status": "open",
  "service_name": "ec2",
  "scenario": "Brief description of the misconfiguration",
  "alert_criteria": "Specific conditions that indicate this misconfiguration exists",
  "recommendation_action": "Clear, actionable recommendation for fixing the issue",
  "risk_detail": "cost",
  "build_priority": 0,
  "action_value": 2,
  "effort_level": 1,
  "risk_value": 2,
  "recommendation_description_detailed": "Detailed explanation of the issue, why it matters, and what happens if not fixed",
  "category": "compute",
  "output_notes": "",
  "notes": "Additional context or special considerations",
  "references": [
    "https://docs.aws.amazon.com/relevant-documentation"
  ],
  "metadata": {
    "created_at": "2025-01-04T00:00:00Z",
    "updated_at": "2025-01-04T00:00:00Z",
    "contributors": ["your-github-username"],
    "source": "Community Contribution"
  },
  "tags": ["tag1", "tag2"],
  "detection_methods": [
    {
      "method": "AWS Config Rule",
      "details": "required-tags"
    }
  ],
  "remediation_examples": [
    {
      "language": "aws-cli",
      "code": "aws ec2 create-tags --resources i-1234567890abcdef0 --tags Key=Name,Value=MyInstance",
      "description": "Add tags to an EC2 instance"
    }
  ]
}
```

### Step 3: Choose the Right File

Add your entry to the appropriate service file in `data/by-service/`:

- For EC2: `data/by-service/ec2.json`
- For S3: `data/by-service/s3.json`
- For Lambda: `data/by-service/lambda.json`
- etc.

If the service doesn't have a file yet, create one with this structure:

```json
{
  "service": "service-name",
  "count": 1,
  "misconfigurations": [
    {
      "your-entry-here": "..."
    }
  ]
}
```

### Step 4: Generate UUID

Generate a UUID for your entry:

```python
import uuid
print(str(uuid.uuid4()))
```

Or use an online UUID generator: https://www.uuidgenerator.net/

## Field Guidelines

### Required Fields

- **id**: UUID v4 format
- **service_name**: AWS service name (lowercase, use hyphens for multi-word)
- **scenario**: Brief, clear description of the issue
- **risk_detail**: One or more of: `cost`, `security`, `operations`, `performance`, `reliability`

### Field Descriptions

- **status**:
  - `open` - New entry, not yet validated
  - `done` - Validated and complete
  - `ice` - On hold, needs more information
  - `pending` - Being worked on

- **build_priority**: 0 (highest) to 3 (lowest)
- **action_value**: Estimated value/impact of fixing (1-3)
- **effort_level**: Estimated effort to fix (1-3)
- **risk_value**: Severity of risk if not fixed (0-3)

- **category**:
  - `compute` - EC2, Lambda, ECS, etc.
  - `networking` - VPC, Route53, CloudFront, etc.
  - `database` - RDS, DynamoDB, etc.
  - `storage` - S3, EBS, etc.
  - `security` - IAM, KMS, etc.

### Writing Good Descriptions

**Scenario** should be:
- Brief (1-2 sentences)
- Specific about what's wrong
- Example: "EC2 instances running on previous generation instance types"

**Alert Criteria** should be:
- Measurable and specific
- Include thresholds where applicable
- Example: "CPU utilization < 5% for 4+ days in last 14 days"

**Recommendation Action** should be:
- Clear and actionable
- Start with a verb
- Example: "Upgrade to current generation instance types (t3, m5, c5, etc.)"

**Detailed Description** should:
- Explain why this matters
- Describe the impact
- Provide context
- Be comprehensive but concise

## Improving Existing Entries

To improve an existing entry:

1. Find the entry in the appropriate service file
2. Make your changes
3. Update the `updated_at` timestamp
4. Add your username to `contributors` array if not already there
5. Follow the submission process below

Common improvements:
- Adding missing references
- Adding detection methods
- Adding remediation examples
- Clarifying descriptions
- Fixing typos or errors
- Adding compliance mappings

## Submission Process

### 1. Fork the Repository

```bash
gh repo fork aws-misconfig-db/aws-misconfig-db
cd aws-misconfig-db
```

### 2. Create a Branch

```bash
git checkout -b add-s3-misconfiguration
```

### 3. Make Your Changes

Edit the appropriate JSON file(s) in `data/by-service/`.

### 4. Validate Your Changes

```bash
# Validate the specific file you changed
python3 scripts/validate.py data/by-service/s3.json

# Or validate everything
python3 scripts/validate.py data/by-service/ --strict
```

### 5. Regenerate Aggregated Files

```bash
python3 scripts/generate.py
```

### 6. Commit Your Changes

```bash
git add data/by-service/s3.json
git add data/all-misconfigs.json
git add data/by-category/
git add data/summary-stats.json
git add docs/SUMMARY.md

git commit -m "Add S3 bucket versioning misconfiguration

- Added new entry for unversioned S3 buckets
- Includes detection method via AWS Config
- Added remediation example with CLI command"
```

### 7. Push and Create Pull Request

```bash
git push origin add-s3-misconfiguration
gh pr create --title "Add S3 bucket versioning misconfiguration" --body "Description of changes"
```

## Style Guidelines

### JSON Formatting

- Use 2-space indentation
- Keep arrays on single line if < 3 items
- Multi-line for longer content
- No trailing commas
- Ensure valid JSON

### Writing Style

- Use clear, professional language
- Be concise but thorough
- Use active voice
- Avoid jargon when possible
- Include examples when helpful

### References

- Prefer official AWS documentation
- Include blog posts or articles from reputable sources
- Ensure links are HTTPS
- Check that links are still valid

## Validation

All submissions must pass validation before being merged:

```bash
python3 scripts/validate.py data/by-service/ --strict
```

The validation checks:
- Required fields are present
- Field types are correct
- Enum values are valid
- UUID format is correct
- Reference URLs are properly formatted

## Review Process

1. **Automated Checks**: GitHub Actions will run validation on your PR
2. **Community Review**: Other contributors may review and comment
3. **Maintainer Review**: A maintainer will do a final review
4. **Feedback**: You may be asked to make changes
5. **Merge**: Once approved, your PR will be merged

Typical review time: 2-7 days

## Questions or Issues?

- **Questions**: Open a [Discussion](https://github.com/aws-misconfig-db/aws-misconfig-db/discussions)
- **Bugs**: Open an [Issue](https://github.com/aws-misconfig-db/aws-misconfig-db/issues)
- **Ideas**: Open an [Issue](https://github.com/aws-misconfig-db/aws-misconfig-db/issues) with the "enhancement" label

## Recognition

Contributors will be:
- Listed in the entry's `contributors` field
- Added to the CONTRIBUTORS.md file
- Acknowledged in release notes

Thank you for contributing to make AWS infrastructure more secure, cost-effective, and reliable!
