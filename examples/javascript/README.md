# JavaScript Examples

This directory contains JavaScript examples for using the AWS Misconfiguration Database in both Node.js and browser environments.

## Examples

### 1. basic_usage.js (Node.js)

Demonstrates basic operations in Node.js:
- Loading the database
- Filtering by risk type, priority, and service
- Searching for keywords
- Querying cost optimizations

**Usage:**
```bash
cd examples/javascript
node basic_usage.js
```

### 2. browser_example.html (Browser)

Interactive web interface for browsing the database.

**Features:**
- Filter by service, risk type, and priority
- Search functionality
- Visual display with badges and colors
- Responsive design

**Usage:**
```bash
# Serve locally
python3 -m http.server 8000
# Then open: http://localhost:8000/examples/javascript/browser_example.html

# Or open the file directly in your browser
open browser_example.html
```

## Integration Patterns

### Loading in Node.js

```javascript
const fs = require('fs');
const path = require('path');

function loadDatabase() {
  const data = fs.readFileSync('../../data/all-misconfigs.json', 'utf8');
  return JSON.parse(data);
}

const db = loadDatabase();
```

### Loading in Browser

```javascript
async function loadDatabase() {
  const response = await fetch('../../data/all-misconfigs.json');
  return await response.json();
}

// Usage
loadDatabase().then(db => {
  console.log(`Loaded ${db.total_count} misconfigurations`);
});
```

### Filtering Examples

```javascript
// Filter by risk type
const securityIssues = db.misconfigurations.filter(m =>
  (m.risk_detail || '').includes('security')
);

// Filter by service
const ec2Issues = db.misconfigurations.filter(m =>
  m.service_name === 'ec2'
);

// Filter by priority (0 = highest)
const criticalIssues = db.misconfigurations.filter(m =>
  m.build_priority === 0
);

// Search by keyword
const searchTerm = 'encryption';
const results = db.misconfigurations.filter(m =>
  (m.scenario || '').toLowerCase().includes(searchTerm.toLowerCase())
);
```

### Sorting Examples

```javascript
// Sort by priority
const sorted = db.misconfigurations.sort((a, b) =>
  (a.build_priority || 99) - (b.build_priority || 99)
);

// Sort cost optimizations by value/effort ratio
const costOpts = db.misconfigurations
  .filter(m => (m.risk_detail || '').includes('cost'))
  .sort((a, b) => {
    const effortA = a.effort_level || 99;
    const effortB = b.effort_level || 99;
    if (effortA !== effortB) return effortA - effortB;
    return (b.action_value || 0) - (a.action_value || 0);
  });
```

## Using with Web Frameworks

### Express.js API

```javascript
const express = require('express');
const fs = require('fs');

const app = express();
const db = JSON.parse(fs.readFileSync('../../data/all-misconfigs.json', 'utf8'));

app.get('/api/misconfigs', (req, res) => {
  res.json(db);
});

app.get('/api/misconfigs/service/:service', (req, res) => {
  const filtered = db.misconfigurations.filter(m =>
    m.service_name === req.params.service
  );
  res.json({ count: filtered.length, misconfigurations: filtered });
});

app.listen(3000, () => {
  console.log('API running on http://localhost:3000');
});
```

### React Component Example

```jsx
import React, { useState, useEffect } from 'react';

function MisconfigViewer() {
  const [misconfigs, setMisconfigs] = useState([]);
  const [filter, setFilter] = useState('');

  useEffect(() => {
    fetch('/data/all-misconfigs.json')
      .then(res => res.json())
      .then(data => setMisconfigs(data.misconfigurations));
  }, []);

  const filtered = misconfigs.filter(m =>
    !filter || m.service_name === filter
  );

  return (
    <div>
      <select onChange={e => setFilter(e.target.value)}>
        <option value="">All Services</option>
        <option value="ec2">EC2</option>
        <option value="s3">S3</option>
        {/* ... */}
      </select>

      {filtered.map(m => (
        <div key={m.id}>
          <h3>{m.scenario}</h3>
          <p>Service: {m.service_name}</p>
          <p>Risk: {m.risk_detail}</p>
          <p>Recommendation: {m.recommendation_action}</p>
        </div>
      ))}
    </div>
  );
}
```

## Additional Resources

- [Main Documentation](../../README.md)
- [Schema Documentation](../../docs/SCHEMA.md)
- [Contributing Guidelines](../../docs/CONTRIBUTING.md)
