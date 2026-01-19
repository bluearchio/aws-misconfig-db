<div align="center">

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║     ▄▄▄       █     █░  ██████                                               ║
║    ▒████▄    ▓█░ █ ░█░▒██    ▒                                               ║
║    ▒██  ▀█▄  ▒█░ █ ░█ ░ ▓██▄                                                 ║
║    ░██▄▄▄▄██ ░█░ █ ░█   ▒   ██▒                                              ║
║     ▓█   ▓██▒░░██▒██▓ ▒██████▒▒                                              ║
║     ▒▒   ▓▒█░░ ▓░▒ ▒  ▒ ▒▓▒ ▒ ░                                              ║
║      ▒   ▒▒ ░  ▒ ░ ░  ░ ░▒  ░ ░                                              ║
║      ░   ▒     ░   ░  ░  ░  ░                                                ║
║          ░  ░    ░          ░                                                ║
║                                                                              ║
║    ███╗   ███╗██╗███████╗ ██████╗ ██████╗ ███╗   ██╗███████╗██╗ ██████╗     ║
║    ████╗ ████║██║██╔════╝██╔════╝██╔═══██╗████╗  ██║██╔════╝██║██╔════╝     ║
║    ██╔████╔██║██║███████╗██║     ██║   ██║██╔██╗ ██║█████╗  ██║██║  ███╗    ║
║    ██║╚██╔╝██║██║╚════██║██║     ██║   ██║██║╚██╗██║██╔══╝  ██║██║   ██║    ║
║    ██║ ╚═╝ ██║██║███████║╚██████╗╚██████╔╝██║ ╚████║██║     ██║╚██████╔╝    ║
║    ╚═╝     ╚═╝╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝     ╚═╝ ╚═════╝     ║
║                                                                              ║
║    ██████╗  █████╗ ████████╗ █████╗ ██████╗  █████╗ ███████╗███████╗        ║
║    ██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔════╝        ║
║    ██║  ██║███████║   ██║   ███████║██████╔╝███████║███████╗█████╗          ║
║    ██║  ██║██╔══██║   ██║   ██╔══██║██╔══██╗██╔══██║╚════██║██╔══╝          ║
║    ██████╔╝██║  ██║   ██║   ██║  ██║██████╔╝██║  ██║███████║███████╗        ║
║    ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝╚══════╝╚══════╝        ║
║                                                                              ║
║                  🔥 313 Recommendations • 41 Services 🔥                     ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

<h3>Production-ready AWS misconfiguration detection & remediation</h3>

<p>
💰 <b>Cost</b> • 🛠️ <b>Operations</b> • ⚡ <b>Performance</b> • 🔐 <b>Security</b> • 🔄 <b>Reliability</b>
</p>

</div>

---

## Database Summary

> *Generated via DuckDB queries against `db/recommendations.duckdb`*

### Total Recommendations
**313** recommendations across **41** AWS services

### By Risk Type
| Risk Type | Count |
|-----------|-------|
| operations | 189 |
| cost | 80 |
| performance | 21 |
| security | 19 |
| reliability | 4 |

### Top 15 Services
| Service | Recommendations |
|---------|-----------------|
| ec2 | 49 |
| general | 32 |
| s3 | 24 |
| lambda | 21 |
| rds | 19 |
| iam | 18 |
| alb/elb | 16 |
| networking | 15 |
| cloudfront | 13 |
| dynamodb | 11 |
| ebs | 10 |
| route 53 | 8 |
| efs | 8 |
| kinesis | 7 |
| ecs | 6 |

### By Priority
| Priority | Count | Description |
|----------|-------|-------------|
| 0 | 61 | Critical |
| 1 | 49 | High |
| 2 | 16 | Medium |
| 3 | 4 | Low |

### By Category
| Category | Count |
|----------|-------|
| cost | 17 |
| security | 8 |
| networking | 7 |
| operations | 6 |
| database | 6 |
| ai | 5 |
| storage | 5 |
| management | 4 |
| compute | 3 |
| messaging | 1 |

---

## What Is This?

A structured, queryable database of AWS misconfigurations and best practices. Use it to:

- **Power LLM-based AWS advisors** - Feed recommendations to Claude, GPT, or your own models
- **Extend cloud management tools** - Integrate with Vantage, Cloud Custodian, Steampipe
- **Build custom scanners** - Create detection rules for your infrastructure
- **Train teams** - Reference material for AWS best practices

---

## Quick Start (2 minutes)

### 1. Clone and Initialize

```bash
git clone https://github.com/bluearchio/aws-misconfig-db.git
cd aws-misconfig-db

# Install DuckDB
pip install duckdb

# Build the queryable database
python3 scripts/db-init.py
```

### 2. Explore Recommendations

```bash
# View full summary
python3 scripts/db-query.py summary

# List recommendations for a service
python3 scripts/db-query.py service ec2
python3 scripts/db-query.py service s3
python3 scripts/db-query.py service lambda

# Search across all recommendations
python3 scripts/db-query.py search "encryption"
python3 scripts/db-query.py search "cost"
python3 scripts/db-query.py search "idle"

# Interactive SQL mode
python3 scripts/db-query.py interactive
```

### 3. Query with SQL

```python
import duckdb

conn = duckdb.connect('db/recommendations.duckdb')

# Top cost optimization opportunities
conn.execute("""
    SELECT service_name, scenario, recommendation_action
    FROM recommendations
    WHERE risk_detail LIKE '%cost%'
    AND build_priority = 0
    ORDER BY service_name
""").fetchdf()

# Security issues by service
conn.execute("""
    SELECT service_name, COUNT(*) as issues
    FROM recommendations
    WHERE risk_detail LIKE '%security%'
    GROUP BY service_name
    ORDER BY issues DESC
""").fetchdf()
```

---

## Integration Examples

### LLM Integration (Claude/GPT)

Use the database as context for an AWS infrastructure advisor:

```python
import duckdb
import anthropic  # or openai

# Load relevant recommendations
conn = duckdb.connect('db/recommendations.duckdb')
recommendations = conn.execute("""
    SELECT service_name, scenario, recommendation_action,
           recommendation_description_detailed, risk_detail
    FROM recommendations
    WHERE service_name IN ('ec2', 's3', 'iam', 'rds')
    AND build_priority <= 1
""").fetchdf().to_dict('records')

# Build context for LLM
context = "You are an AWS infrastructure advisor. Use these recommendations:\n\n"
for rec in recommendations:
    context += f"**{rec['service_name'].upper()}**: {rec['scenario']}\n"
    context += f"Action: {rec['recommendation_action']}\n"
    context += f"Risk: {rec['risk_detail']}\n\n"

# Query with Claude
client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    system=context,
    messages=[{"role": "user", "content": "Review my EC2 setup: I have 50 instances, 20 are t2.micro running 24/7, no auto-scaling, and EBS volumes are unencrypted."}]
)
print(response.content[0].text)
```

### Vantage Integration

Export recommendations as Vantage-compatible cost insights:

```python
import duckdb
import json

conn = duckdb.connect('db/recommendations.duckdb')

# Get cost recommendations in Vantage-friendly format
cost_recs = conn.execute("""
    SELECT
        id,
        service_name as resource_type,
        scenario as title,
        recommendation_action as recommendation,
        recommendation_description_detailed as description,
        CASE build_priority
            WHEN 0 THEN 'critical'
            WHEN 1 THEN 'high'
            WHEN 2 THEN 'medium'
            ELSE 'low'
        END as priority
    FROM recommendations
    WHERE risk_detail LIKE '%cost%'
""").fetchdf()

# Export for Vantage custom reports
vantage_insights = []
for _, rec in cost_recs.iterrows():
    vantage_insights.append({
        "category": "cost_optimization",
        "resource_type": f"aws:{rec['resource_type']}",
        "title": rec['title'],
        "recommendation": rec['recommendation'],
        "priority": rec['priority'],
        "source": "aws-misconfig-db"
    })

with open('vantage-insights.json', 'w') as f:
    json.dump(vantage_insights, f, indent=2)

print(f"Exported {len(vantage_insights)} cost insights for Vantage")
```

### Cloud Custodian Policies

Generate Cloud Custodian policies from recommendations:

```python
import duckdb
import yaml

conn = duckdb.connect('db/recommendations.duckdb')

# Get EC2 security recommendations
ec2_security = conn.execute("""
    SELECT scenario, alert_criteria, recommendation_action
    FROM recommendations
    WHERE service_name = 'ec2'
    AND risk_detail LIKE '%security%'
""").fetchdf()

# Generate Custodian policies
policies = {"policies": []}

# Example: Unencrypted EBS volumes
policies["policies"].append({
    "name": "ec2-unencrypted-volumes",
    "resource": "ebs",
    "description": "Flag unencrypted EBS volumes (from aws-misconfig-db)",
    "filters": [
        {"Encrypted": False}
    ],
    "actions": [
        {"type": "notify",
         "template": "Unencrypted EBS volume detected",
         "transport": {"type": "sns", "topic": "arn:aws:sns:us-east-1:123456789:alerts"}}
    ]
})

# Example: Unused Elastic IPs
policies["policies"].append({
    "name": "ec2-unused-elastic-ips",
    "resource": "network-addr",
    "description": "Find unassociated Elastic IPs (from aws-misconfig-db)",
    "filters": [
        {"AssociationId": "absent"}
    ],
    "actions": [
        {"type": "notify",
         "template": "Unassociated Elastic IP found - wasting $3.65/month",
         "transport": {"type": "sns", "topic": "arn:aws:sns:us-east-1:123456789:alerts"}}
    ]
})

with open('custodian-policies.yml', 'w') as f:
    yaml.dump(policies, f, default_flow_style=False)

print("Generated Cloud Custodian policies")
```

### Steampipe Integration

Query recommendations alongside live AWS data:

```sql
-- In Steampipe, create a foreign table from the DuckDB export
-- First, export to CSV:
-- python3 -c "import duckdb; duckdb.connect('db/recommendations.duckdb').execute('COPY recommendations TO \"recommendations.csv\" (HEADER, DELIMITER \",\")').fetchall()"

-- Then in Steampipe:
CREATE FOREIGN TABLE aws_recommendations (
    id text,
    service_name text,
    scenario text,
    recommendation_action text,
    risk_detail text,
    build_priority int
) SERVER steampipe OPTIONS (filename '/path/to/recommendations.csv', format 'csv', header 'true');

-- Join with live EC2 data
SELECT
    i.instance_id,
    i.instance_type,
    r.scenario,
    r.recommendation_action
FROM aws_ec2_instance i
CROSS JOIN aws_recommendations r
WHERE r.service_name = 'ec2'
AND r.scenario LIKE '%idle%'
AND i.cpu_utilization_average < 5;
```

### AWS Config Rules

Generate AWS Config custom rules:

```python
import duckdb
import json

conn = duckdb.connect('db/recommendations.duckdb')

# Get recommendations with detection methods
detectable = conn.execute("""
    SELECT service_name, scenario, alert_criteria, detection_methods
    FROM recommendations
    WHERE detection_methods != '[]'
    AND alert_criteria != ''
""").fetchdf()

# Generate Config rule skeletons
config_rules = []
for _, rec in detectable.iterrows():
    methods = json.loads(rec['detection_methods'])
    for method in methods:
        if method.get('method') == 'CloudWatch Metric':
            config_rules.append({
                "ConfigRuleName": f"misconfig-{rec['service_name']}-check",
                "Description": rec['scenario'][:256],
                "Source": {
                    "Owner": "CUSTOM_LAMBDA",
                    "SourceIdentifier": "arn:aws:lambda:REGION:ACCOUNT:function:config-rule-checker"
                },
                "InputParameters": json.dumps({
                    "alert_criteria": rec['alert_criteria'],
                    "detection_details": method.get('details', '')
                })
            })

print(f"Generated {len(config_rules)} AWS Config rule templates")
```

---

## Database Schema

Each recommendation contains:

| Field | Description |
|-------|-------------|
| `id` | Unique UUID |
| `service_name` | AWS service (ec2, s3, lambda, etc.) |
| `scenario` | What the misconfiguration is |
| `alert_criteria` | When to trigger an alert |
| `recommendation_action` | What to do about it |
| `risk_detail` | Risk type(s): cost, security, operations, performance, reliability |
| `build_priority` | 0 (critical) to 3 (low) |
| `recommendation_description_detailed` | Full explanation |
| `category` | Resource category (compute, storage, database, etc.) |
| `references` | AWS documentation links |
| `architectural_patterns` | Related design patterns (Circuit Breaker, Cache-Aside, etc.) |
| `detection_methods` | How to detect (CloudWatch, CLI, API) |
| `remediation_examples` | Code examples (Python, Terraform, AWS CLI) |

---

## Repository Structure

```
aws-misconfig-db/
├── data/by-service/        # Source of truth (41 JSON files)
│   ├── ec2.json            # 49 recommendations
│   ├── s3.json             # 24 recommendations
│   ├── lambda.json         # 21 recommendations
│   └── ...
├── db/                     # Generated DuckDB database
├── scripts/
│   ├── db-init.py          # Build the database
│   ├── db-query.py         # Query helper CLI
│   ├── validate.py         # Schema validation
│   └── generate.py         # Generate SUMMARY.md
└── schema/
    └── misconfig-schema.json
```

---

## Common Queries

```sql
-- All high-priority cost issues
SELECT service_name, scenario, recommendation_action
FROM recommendations
WHERE risk_detail LIKE '%cost%' AND build_priority = 0;

-- Security issues with remediation code
SELECT service_name, scenario, remediation_examples
FROM recommendations
WHERE risk_detail LIKE '%security%' AND remediation_examples != '[]';

-- Recommendations by architectural pattern
SELECT r.service_name, r.scenario,
       json_extract_string(p.pattern, '$.pattern_name') as pattern
FROM recommendations r,
     LATERAL unnest(json_extract(r.architectural_patterns, '$[*]')) as p(pattern)
WHERE r.architectural_patterns != '[]';

-- Services with most recommendations
SELECT service_name, COUNT(*) as count
FROM recommendations
GROUP BY service_name
ORDER BY count DESC
LIMIT 10;
```

---

## Contributing

```bash
# Validate your changes
python3 scripts/validate.py data/by-service/

# Rebuild database
python3 scripts/db-init.py

# Update documentation
python3 scripts/generate.py
```

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

---

## License

MIT License - see [LICENSE](LICENSE)

---

<div align="center">

**🔥 313 recommendations • 41 services • Query with SQL • Integrate anywhere 🔥**

</div>
