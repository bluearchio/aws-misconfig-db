# AWS Misconfiguration Database

A comprehensive, community-driven database of AWS misconfigurations, designed to be LLM-friendly and easily integrated into security tools, cost optimization platforms, and infrastructure analysis systems.

## Overview

This repository contains a structured database of AWS misconfigurations covering:

- **Security** vulnerabilities and best practices
- **Cost optimization** opportunities
- **Performance** improvements
- **Reliability** enhancements
- **Operational** best practices

The database is designed with a standardized JSON format, making it ideal for:
- Training and fine-tuning LLMs for AWS infrastructure analysis
- Building automated security and compliance scanning tools
- Creating cost optimization recommendations
- Developing infrastructure analysis platforms
- Educational purposes and AWS best practices reference

## Database Statistics

- **Total Misconfigurations**: 251+
- **AWS Services Covered**: 21+
- **Risk Categories**: Security, Cost, Performance, Operations, Reliability
- **Status**: Done (23), In-Progress (10), Open (209), Pending (9)

See [docs/SUMMARY.md](docs/SUMMARY.md) for detailed statistics.

## Repository Structure

```
├── data/
│   ├── by-service/          # Organized by AWS service (ec2, s3, rds, etc.)
│   ├── by-category/         # Organized by risk type (cost, security, etc.)
│   └── all-misconfigs.json  # Complete unified dataset
├── schema/
│   └── misconfig-schema.json  # JSON Schema definition
├── scripts/
│   ├── validate.py          # Validate entries against schema
│   ├── generate.py          # Generate aggregated files
│   └── import-csv.py        # Import from CSV format
├── examples/
│   ├── python/              # Python integration examples
│   ├── javascript/          # JavaScript integration examples
│   └── llm-prompts/         # LLM prompt templates
└── docs/
    ├── SCHEMA.md            # Schema documentation
    ├── CONTRIBUTING.md      # Contribution guidelines
    └── SUMMARY.md           # Database statistics
```

## Quick Start

### Accessing the Data

**Load all misconfigurations:**
```bash
curl https://raw.githubusercontent.com/[your-org]/aws-misconfig-db/main/data/all-misconfigs.json
```

**Load by service (e.g., EC2):**
```bash
curl https://raw.githubusercontent.com/[your-org]/aws-misconfig-db/main/data/by-service/ec2.json
```

**Load by risk type (e.g., security):**
```bash
curl https://raw.githubusercontent.com/[your-org]/aws-misconfig-db/main/data/by-category/security.json
```

### Python Example

```python
import json
import requests

# Load all misconfigurations
response = requests.get('https://raw.githubusercontent.com/[your-org]/aws-misconfig-db/main/data/all-misconfigs.json')
data = response.json()

# Filter by service
ec2_misconfigs = [m for m in data['misconfigurations'] if m['service_name'] == 'ec2']

# Filter by risk type
security_issues = [m for m in data['misconfigurations'] if 'security' in m.get('risk_detail', '')]

print(f"Found {len(ec2_misconfigs)} EC2 misconfigurations")
print(f"Found {len(security_issues)} security-related issues")
```

### JavaScript Example

```javascript
const fetch = require('node-fetch');

async function loadMisconfigs() {
  const response = await fetch('https://raw.githubusercontent.com/[your-org]/aws-misconfig-db/main/data/all-misconfigs.json');
  const data = await response.json();

  // Filter high-priority issues
  const highPriority = data.misconfigurations.filter(m => m.build_priority === 0);

  console.log(`Found ${highPriority.length} high-priority issues`);
}

loadMisconfigs();
```

## Data Format

Each misconfiguration entry follows this structure:

```json
{
  "id": "uuid",
  "status": "done|ice|open|pending",
  "service_name": "ec2",
  "scenario": "Description of the misconfiguration",
  "alert_criteria": "Conditions that trigger this alert",
  "recommendation_action": "Recommended remediation action",
  "risk_detail": "cost|security|operations|performance|reliability",
  "build_priority": 0,
  "action_value": 1,
  "effort_level": 1,
  "risk_value": 2,
  "recommendation_description_detailed": "Detailed explanation",
  "category": "compute|networking|database|storage|security",
  "notes": "Additional context",
  "references": [
    "https://docs.aws.amazon.com/..."
  ],
  "metadata": {
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z",
    "contributors": ["username"],
    "source": "AWS Trusted Advisor"
  }
}
```

See [docs/SCHEMA.md](docs/SCHEMA.md) for complete schema documentation.

## Use Cases

### 1. LLM Training & Fine-tuning

```python
# Example: Prepare data for LLM training
for misconfig in data['misconfigurations']:
    prompt = f"Service: {misconfig['service_name']}\nIssue: {misconfig['scenario']}"
    response = f"Recommendation: {misconfig['recommendation_action']}\nRisk: {misconfig['risk_detail']}"
    # Feed to your training pipeline
```

### 2. Security Scanning Tool

```python
def check_unencrypted_volumes(aws_client, misconfig_db):
    # Load relevant misconfiguration
    unencrypted_rule = next(
        m for m in misconfig_db
        if 'unencrypted volumes' in m['scenario'].lower()
    )

    # Apply detection logic
    volumes = aws_client.describe_volumes()
    for vol in volumes:
        if not vol['Encrypted']:
            return {
                'finding': unencrypted_rule,
                'resource': vol['VolumeId'],
                'severity': unencrypted_rule['risk_value']
            }
```

### 3. Cost Optimization Recommendations

```python
# Find all cost-related misconfigurations
cost_optimizations = [
    m for m in data['misconfigurations']
    if 'cost' in m.get('risk_detail', '')
]

# Prioritize by effort vs value
sorted_opts = sorted(
    cost_optimizations,
    key=lambda x: (x.get('effort_level', 99), -x.get('action_value', 0))
)
```

## Development

### Prerequisites

- Python 3.8+
- pip (for Python dependencies)

### Setup

```bash
# Clone the repository
git clone https://github.com/[your-org]/aws-misconfig-db.git
cd aws-misconfig-db

# Validate the database
python3 scripts/validate.py data/

# Generate aggregated files
python3 scripts/generate.py
```

### Validation

```bash
# Validate all entries
python3 scripts/validate.py data/by-service/

# Validate specific file
python3 scripts/validate.py data/by-service/ec2.json

# Strict mode (exit with error on validation failure)
python3 scripts/validate.py --strict data/
```

## Contributing

We welcome contributions from the community! Please see [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines on:

- Adding new misconfiguration entries
- Improving existing entries
- Suggesting new categories or services
- Reporting issues

## Schema Validation

All entries are validated against a JSON Schema. The schema ensures:

- Required fields are present
- Data types are correct
- Enum values are valid
- UUID format is correct
- Reference URLs are valid

Run validation before submitting PRs:

```bash
python3 scripts/validate.py data/by-service/
```

## Integration Examples

See the [examples/](examples/) directory for complete integration examples:

- **Python**: Loading, filtering, and analyzing misconfigurations
- **JavaScript**: Node.js and browser-based integration
- **LLM Prompts**: Template prompts for various use cases

## Roadmap

- [ ] Add CVE references for security-related misconfigurations
- [ ] Include compliance framework mappings (PCI-DSS, HIPAA, SOC2, etc.)
- [ ] Add detection methods (AWS Config rules, CLI commands, etc.)
- [ ] Include remediation code examples (Terraform, CloudFormation, Python)
- [ ] Create API for querying the database
- [ ] Add severity scoring system
- [ ] Community voting on priority and impact

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Initial data sourced from AWS Trusted Advisor recommendations
- Community contributors (see [CONTRIBUTORS.md](CONTRIBUTORS.md))
- Inspired by the OWASP Top 10 and CIS Benchmarks

## Support

- **Issues**: [GitHub Issues](https://github.com/[your-org]/aws-misconfig-db/issues)
- **Discussions**: [GitHub Discussions](https://github.com/[your-org]/aws-misconfig-db/discussions)
- **Security Issues**: Please email security@[your-domain].com

## Citation

If you use this database in your research or project, please cite:

```bibtex
@misc{aws-misconfig-db,
  title={AWS Misconfiguration Database},
  author={Your Organization},
  year={2025},
  url={https://github.com/[your-org]/aws-misconfig-db}
}
```

---

**Last Updated**: 2025-01-04
**Version**: 1.0.0
**Total Entries**: 251
