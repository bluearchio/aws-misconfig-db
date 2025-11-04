---
name: New Misconfiguration Entry
about: Submit a new AWS misconfiguration to the database
title: '[NEW] '
labels: 'new-entry'
assignees: ''
---

## Misconfiguration Details

**AWS Service:**
<!-- e.g., ec2, s3, rds, lambda -->

**Scenario:**
<!-- Brief description of the misconfiguration (1-2 sentences) -->

**Risk Type:**
<!-- Choose one or more: cost, security, operations, performance, reliability -->

**Priority:**
<!-- 0 (Critical), 1 (High), 2 (Medium), 3 (Low) -->

## Detection

**Alert Criteria:**
<!-- How to detect this misconfiguration? Include specific metrics or conditions -->

**Detection Method:**
<!-- e.g., AWS Config Rule, CloudWatch Metric, CLI Command -->

```bash
# If applicable, provide detection command/script
```

## Remediation

**Recommended Action:**
<!-- Clear, actionable recommendation -->

**Detailed Description:**
<!-- Comprehensive explanation of why this matters and the impact -->

**Effort Level:**
<!-- 0 (Minimal), 1 (Low), 2 (Medium), 3 (High) -->

**Expected Value/Impact:**
<!-- 1 (Low), 2 (Medium), 3 (High) -->

## References

<!-- Provide links to AWS documentation or other authoritative sources -->
- [ ] AWS Documentation:
- [ ] Blog Post/Article:
- [ ] Other:

## Remediation Examples

<!-- If you have code examples for fixing this issue, please provide them -->

**AWS CLI:**
```bash
# Command to remediate
```

**Terraform:**
```hcl
# Terraform configuration
```

**Python (boto3):**
```python
# Python script
```

## Compliance Mapping

<!-- If applicable, which compliance frameworks does this relate to? -->
- [ ] PCI-DSS
- [ ] HIPAA
- [ ] SOC2
- [ ] CIS Benchmark
- [ ] NIST
- [ ] Other:

## Additional Context

<!-- Any other information that would be helpful -->

## Checklist

- [ ] I have searched the existing database to ensure this is not a duplicate
- [ ] I have provided clear detection criteria
- [ ] I have included at least one reference link
- [ ] I have tested the remediation steps (if applicable)
- [ ] I understand this will be reviewed before being merged
