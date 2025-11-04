# Python Examples

This directory contains Python examples demonstrating how to use the AWS Misconfiguration Database.

## Examples

### 1. basic_usage.py

Demonstrates basic operations:
- Loading the database
- Filtering by risk type, priority, and service
- Searching for keywords
- Querying cost optimizations

**Usage:**
```bash
cd examples/python
python3 basic_usage.py
```

### 2. aws_scanner.py

Shows how to integrate with AWS boto3 to scan actual infrastructure for misconfigurations.

**Prerequisites:**
```bash
pip install boto3
```

**Usage:**
```bash
# Using default AWS credentials
python3 aws_scanner.py --region us-east-1

# Using specific AWS profile
python3 aws_scanner.py --profile my-profile --region us-west-2

# Save report to file
python3 aws_scanner.py --output scan_results.json
```

**Features:**
- Scans for unencrypted EBS volumes
- Detects unattached Elastic IPs
- Finds old IAM access keys (90+ days)
- Generates detailed findings report

## Integration Patterns

### Loading the Database

```python
import json

def load_database(file_path="../../data/all-misconfigs.json"):
    with open(file_path, 'r') as f:
        return json.load(f)

db = load_database()
misconfigs = db['misconfigurations']
```

### Filtering by Risk Type

```python
security_issues = [
    m for m in misconfigs
    if 'security' in m.get('risk_detail', '')
]
```

### Filtering by Service

```python
ec2_issues = [
    m for m in misconfigs
    if m.get('service_name') == 'ec2'
]
```

### Searching by Keyword

```python
def search(misconfigs, keyword):
    keyword_lower = keyword.lower()
    return [
        m for m in misconfigs
        if keyword_lower in m.get('scenario', '').lower()
        or keyword_lower in m.get('recommendation_description_detailed', '').lower()
    ]

encryption_items = search(misconfigs, 'encryption')
```

### Prioritization

```python
# Get high-priority, low-effort fixes
quick_wins = [
    m for m in misconfigs
    if m.get('build_priority', 99) <= 1  # High priority
    and m.get('effort_level', 99) <= 1   # Low effort
]

sorted_wins = sorted(
    quick_wins,
    key=lambda x: (x.get('effort_level', 99), -x.get('action_value', 0))
)
```

## Using with Web Frameworks

### Flask Example

```python
from flask import Flask, jsonify
import json

app = Flask(__name__)

# Load database at startup
with open('../../data/all-misconfigs.json') as f:
    DB = json.load(f)

@app.route('/api/misconfigs')
def get_misconfigs():
    return jsonify(DB)

@app.route('/api/misconfigs/service/<service>')
def get_by_service(service):
    filtered = [
        m for m in DB['misconfigurations']
        if m.get('service_name') == service
    ]
    return jsonify({'count': len(filtered), 'misconfigurations': filtered})

if __name__ == '__main__':
    app.run(debug=True)
```

### FastAPI Example

```python
from fastapi import FastAPI
import json

app = FastAPI()

with open('../../data/all-misconfigs.json') as f:
    DB = json.load(f)

@app.get("/api/misconfigs")
async def get_misconfigs():
    return DB

@app.get("/api/misconfigs/service/{service}")
async def get_by_service(service: str):
    filtered = [
        m for m in DB['misconfigurations']
        if m.get('service_name') == service
    ]
    return {'count': len(filtered), 'misconfigurations': filtered}
```

## Additional Resources

- [Main Documentation](../../README.md)
- [Schema Documentation](../../docs/SCHEMA.md)
- [Contributing Guidelines](../../docs/CONTRIBUTING.md)
