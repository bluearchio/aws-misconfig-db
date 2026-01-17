<div align="center">

```
   ╔═══════════════════════════════════════════════════════════════╗
   ║                                                               ║
   ║      █████╗ ██╗    ██╗███████╗    ███╗   ███╗██████╗        ║
   ║     ██╔══██╗██║    ██║██╔════╝    ████╗ ████║██╔══██╗       ║
   ║     ███████║██║ █╗ ██║███████╗    ██╔████╔██║██║  ██║       ║
   ║     ██╔══██║██║███╗██║╚════██║    ██║╚██╔╝██║██║  ██║       ║
   ║     ██║  ██║╚███╔███╔╝███████║    ██║ ╚═╝ ██║██████╔╝       ║
   ║     ╚═╝  ╚═╝ ╚══╝╚══╝ ╚══════╝    ╚═╝     ╚═╝╚═════╝        ║
   ║                                                               ║
   ║           Misconfiguration Database & Knowledge Hub          ║
   ║                                                               ║
   ╚═══════════════════════════════════════════════════════════════╝
```

<h1>AWS Misconfiguration Database</h1>

<p>
  <a href="https://github.com/bluearchio/aws-misconfig-db/actions"><img src="https://github.com/bluearchio/aws-misconfig-db/workflows/Validate%20Database/badge.svg" alt="Validation Status"></a>
  <a href="https://github.com/bluearchio/aws-misconfig-db/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License"></a>
  <a href="https://github.com/bluearchio/aws-misconfig-db/graphs/contributors"><img src="https://img.shields.io/github/contributors/bluearchio/aws-misconfig-db.svg" alt="Contributors"></a>
  <a href="https://github.com/bluearchio/aws-misconfig-db/issues"><img src="https://img.shields.io/github/issues/bluearchio/aws-misconfig-db.svg" alt="Issues"></a>
</p>

<p><strong>A comprehensive, community-driven database of AWS misconfigurations</strong></p>

<p>
🔐 Security • 💰 Cost • ⚡ Performance • 🛠️ Operations • 🔄 Reliability
</p>

<p>
Designed to be LLM-friendly and easily integrated into security tools, cost optimization platforms, and infrastructure analysis systems.
</p>

</div>

---

## Overview

This repository contains a structured database of AWS misconfigurations covering:

- **Security** vulnerabilities and best practices
- **Cost optimization** opportunities
- **Performance** improvements
- **Reliability** enhancements
- **Operational** best practices
- **Architectural patterns** mapping and implementation guidance

The database is designed with a standardized JSON format, making it ideal for:
- Training and fine-tuning LLMs for AWS infrastructure analysis
- Building automated security and compliance scanning tools
- Creating cost optimization recommendations
- Developing infrastructure analysis platforms
- Educational purposes and AWS best practices reference

## Database Statistics

- **Total Recommendations**: 313
- **AWS Services Covered**: 41
- **Risk Categories**: Security, Cost, Performance, Operations, Reliability
- **Architectural Patterns**: Circuit Breaker, Retry with Exponential Backoff, Cache-Aside, Bulkhead, Queue-Based Load Leveling

See [docs/SUMMARY.md](docs/SUMMARY.md) for detailed statistics.

## Repository Structure

```
├── data/
│   └── by-service/           # Source of truth - organized by AWS service
│       ├── ec2.json          # EC2 recommendations (49 entries)
│       ├── s3.json           # S3 recommendations (24 entries)
│       ├── lambda.json       # Lambda recommendations (21 entries)
│       ├── rds.json          # RDS recommendations (19 entries)
│       ├── iam.json          # IAM recommendations (18 entries)
│       └── ...               # 41 service files total
├── db/
│   └── recommendations.duckdb  # DuckDB database for querying
├── schema/
│   └── misconfig-schema.json   # JSON Schema definition
├── scripts/
│   ├── validate.py           # Validate entries against schema
│   ├── generate.py           # Generate docs/SUMMARY.md
│   ├── classify-general.py   # Classify entries by service
│   └── db-init.py            # Initialize DuckDB database
├── examples/
│   ├── python/               # Python integration examples
│   ├── javascript/           # JavaScript integration examples
│   └── llm-prompts/          # LLM prompt templates
└── docs/
    ├── SCHEMA.md             # Schema documentation
    ├── CONTRIBUTING.md       # Contribution guidelines
    └── SUMMARY.md            # Database statistics
```

## Quick Start

### Accessing the Data

**Load by service (e.g., EC2):**
```bash
curl https://raw.githubusercontent.com/bluearchio/aws-misconfig-db/main/data/by-service/ec2.json
```

**Load all services via script:**
```bash
# Clone and use DuckDB for queries
git clone https://github.com/bluearchio/aws-misconfig-db.git
cd aws-misconfig-db
python3 scripts/db-init.py
```

### Python Example

```python
import json
from pathlib import Path

# Load all recommendations from by-service files
def load_all_recommendations():
    entries = []
    for json_file in Path('data/by-service').glob('*.json'):
        with open(json_file) as f:
            data = json.load(f)
            entries.extend(data.get('misconfigurations', []))
    return entries

data = load_all_recommendations()

# Filter by service
ec2_misconfigs = [m for m in data if m['service_name'] == 'ec2']

# Filter by risk type
security_issues = [m for m in data if 'security' in m.get('risk_detail', '')]

# Filter by architectural pattern
circuit_breaker_misconfigs = [
    m for m in data
    if any(p.get('pattern_name') == 'Circuit Breaker'
           for p in m.get('architectural_patterns', []))
]

print(f"Found {len(ec2_misconfigs)} EC2 misconfigurations")
print(f"Found {len(security_issues)} security-related issues")
print(f"Found {len(circuit_breaker_misconfigs)} Circuit Breaker pattern issues")
```

### DuckDB Example

```python
import duckdb

# Connect to the database
conn = duckdb.connect('db/recommendations.duckdb')

# Query summary stats
print(conn.execute("""
    SELECT service_name, COUNT(*) as count
    FROM recommendations
    GROUP BY service_name
    ORDER BY count DESC
    LIMIT 10
""").fetchdf())

# Find security issues
print(conn.execute("""
    SELECT service_name, scenario
    FROM recommendations
    WHERE risk_detail LIKE '%security%'
""").fetchdf())
```

## Data Format

Each misconfiguration entry follows this structure:

```json
{
  "id": "a1b2c3d4-e5f6-4789-a012-3456789abcde",
  "status": "done|ice|open|pending",
  "service_name": "lambda",
  "scenario": "Lambda functions making synchronous calls without circuit breaker implementation",
  "alert_criteria": "Lambda error rate >5% or downstream service timeouts >1000ms",
  "recommendation_action": "Implement circuit breaker pattern to prevent cascading failures",
  "risk_detail": "reliability, performance",
  "build_priority": 1,
  "action_value": 3,
  "effort_level": 2,
  "risk_value": 2,
  "recommendation_description_detailed": "Circuit breaker prevents repeated calls to failing services...",
  "category": "compute",
  "references": [
    "https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html"
  ],
  "metadata": {
    "created_at": "2025-11-06T20:44:23.794745+00:00",
    "updated_at": "2025-11-06T20:44:23.794745+00:00",
    "contributors": ["pattern-integration-2025"],
    "source": "AWS Prescriptive Guidance - Cloud Design Patterns"
  },
  "tags": ["pattern:circuit-breaker", "resilience-pattern"],
  "architectural_patterns": [
    {
      "pattern_name": "Circuit Breaker",
      "relationship": "missing_implementation",
      "description": "Lambda lacks circuit breaker for downstream service calls"
    }
  ],
  "pattern_implementation_guidance": "Implement using: 1) Lambda Layer with pybreaker library...",
  "detection_methods": [
    {
      "method": "CloudWatch Metric",
      "details": "Lambda Errors metric >5%"
    }
  ],
  "remediation_examples": [
    {
      "language": "python",
      "code": "from pybreaker import CircuitBreaker\nbreaker = CircuitBreaker(fail_max=5)...",
      "description": "Python implementation using pybreaker library"
    }
  ]
}
```

### Architectural Patterns

The database includes mappings to these cloud design patterns:

| Pattern | Description | Relationship Types |
|---------|-------------|-------------------|
| **Circuit Breaker** | Prevent cascading failures by stopping calls to failing services | missing_implementation, incorrect_implementation |
| **Retry with Exponential Backoff** | Handle transient failures with intelligent retry logic | missing_implementation, incorrect_implementation |
| **Cache-Aside** | Reduce database load by caching frequently accessed data | missing_implementation |
| **Bulkhead** | Isolate resources to prevent failures from spreading | missing_implementation |
| **Queue-Based Load Leveling** | Buffer traffic spikes with message queues | missing_implementation |

See [docs/SCHEMA.md](docs/SCHEMA.md) for complete schema documentation.

## Development

### Prerequisites

- Python 3.8+
- DuckDB (`pip install duckdb`)

### Setup

```bash
# Clone the repository
git clone https://github.com/bluearchio/aws-misconfig-db.git
cd aws-misconfig-db

# Validate the database
python3 scripts/validate.py data/by-service/

# Initialize DuckDB database
python3 scripts/db-init.py

# Generate documentation
python3 scripts/generate.py
```

### Validation

```bash
# Validate all entries
python3 scripts/validate.py data/by-service/

# Validate specific file
python3 scripts/validate.py data/by-service/ec2.json
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines on:

- Adding new misconfiguration entries
- Improving existing entries
- Suggesting new categories or services

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Last Updated**: 2026-01-17
**Version**: 2.0.0
**Total Entries**: 313
