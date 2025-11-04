# LLM Prompt Templates for AWS Misconfiguration Analysis

This document contains prompt templates for using the AWS Misconfiguration Database with Large Language Models.

## 1. Infrastructure Analysis Prompt

**Use Case**: Analyze AWS infrastructure configuration and identify potential misconfigurations.

```
You are an AWS infrastructure security and cost optimization expert. I will provide you with AWS resource configurations, and you should analyze them against the AWS Misconfiguration Database to identify issues.

Database Context:
{insert relevant misconfigurations from database as JSON}

Resource Configuration:
{insert AWS resource configuration}

Please analyze the configuration and:
1. Identify any misconfigurations that match entries in the database
2. Assess the severity and risk type (security, cost, performance, operations, reliability)
3. Provide specific remediation recommendations
4. Prioritize findings by risk and effort level
5. Include reference links where applicable

Format your response as:
- Finding ID
- Service
- Issue Description
- Risk Type and Severity
- Current Configuration Problem
- Recommended Action
- Expected Benefits
- Implementation Effort
- References
```

## 2. Cost Optimization Recommendations

**Use Case**: Generate cost optimization recommendations based on AWS usage patterns.

```
You are an AWS cost optimization consultant. Using the AWS Misconfiguration Database, analyze the following AWS account metrics and provide cost optimization recommendations.

Cost Optimization Misconfigurations from Database:
{filter database for risk_detail="cost" and insert as JSON}

Current AWS Usage Patterns:
- EC2 Instance Hours: {hours}
- Average CPU Utilization: {percentage}
- EBS Volume Usage: {GB}
- Unattached EBS Volumes: {count}
- Elastic IP Addresses: {count}
- Reserved Instance Coverage: {percentage}

Tasks:
1. Match usage patterns to relevant cost misconfiguration rules
2. Calculate potential monthly savings for each recommendation
3. Prioritize by ROI (savings vs. implementation effort)
4. Provide implementation roadmap
5. Identify quick wins (low effort, high value)

Output Format:
For each recommendation provide:
- Estimated Monthly Savings
- Implementation Effort (Low/Medium/High)
- Risk Level of Implementation
- Step-by-step Action Plan
- Relevant Database Entry ID
```

## 3. Security Audit Prompt

**Use Case**: Conduct security audit based on AWS best practices.

```
You are an AWS security auditor conducting a security assessment. Use the AWS Misconfiguration Database as your baseline for security best practices.

Security Misconfigurations from Database:
{filter database for risk_detail="security" and insert as JSON}

AWS Account Configuration to Audit:
{insert AWS Config output or resource list}

Audit Tasks:
1. Identify security misconfigurations matching database entries
2. Assess compliance with security frameworks (PCI-DSS, HIPAA, SOC2)
3. Categorize findings by severity (Critical, High, Medium, Low)
4. Map findings to CIS AWS Foundations Benchmark controls
5. Provide remediation timeline recommendations

Required Output:
- Executive Summary
- Detailed Findings List
- Compliance Gap Analysis
- Remediation Priority Matrix
- Timeline and Resource Estimates
```

## 4. Training Data Generation

**Use Case**: Generate training data for fine-tuning LLMs on AWS infrastructure analysis.

```
Using the AWS Misconfiguration Database, generate training examples for an LLM to learn AWS infrastructure analysis.

Database Entry:
{single misconfiguration entry as JSON}

Generate the following training examples:
1. Question-Answer pairs
2. Configuration analysis examples
3. Remediation instruction sequences
4. Risk assessment scenarios

Example Format:

Q: "I have an EC2 instance with {specific configuration}. Are there any issues?"
A: "Based on AWS best practices, this configuration has the following issue: {scenario}.
    Risk Type: {risk_detail}
    Severity: {risk_value}
    Recommendation: {recommendation_action}
    Detailed Explanation: {recommendation_description_detailed}
    References: {references}"

Generate 5 variations of each type with different phrasing and scenarios.
```

## 5. Automated Remediation Script Generation

**Use Case**: Generate infrastructure-as-code for remediating misconfigurations.

```
You are an AWS infrastructure automation engineer. Generate remediation code for the identified misconfiguration.

Misconfiguration Entry:
{single entry with detection_methods and remediation_examples}

Current State:
{description of current misconfiguration}

Generate:
1. Terraform code to remediate the issue
2. AWS CLI commands for manual remediation
3. Python boto3 script for automated remediation
4. CloudFormation template snippet
5. Verification steps to confirm remediation

Include:
- Inline comments explaining each step
- Error handling
- Rollback procedures
- Testing recommendations
- Compliance validation
```

## 6. Real-time Advisory System

**Use Case**: Provide real-time recommendations during infrastructure provisioning.

```
You are an AWS advisory system that provides real-time recommendations during resource provisioning.

Proposed Resource Configuration:
{resource configuration being created/modified}

Relevant Misconfigurations:
{filter database by service_name and insert matching entries}

Analyze the proposed configuration and:
1. Identify potential issues before deployment
2. Suggest configuration improvements
3. Highlight security concerns
4. Recommend cost-optimized alternatives
5. Provide compliance considerations

Response Format:
- Status: [APPROVED | APPROVED_WITH_WARNINGS | REQUIRES_CHANGES | BLOCKED]
- Issues Found: [list]
- Recommended Changes: [specific modifications]
- Alternative Configurations: [better options]
- Estimated Cost Impact: [monthly cost comparison]
- Security Score: [0-100]
```

## 7. Comparative Analysis

**Use Case**: Compare multiple configuration options or accounts.

```
Compare these AWS configurations and recommend the best approach based on the misconfiguration database.

Configuration A:
{config details}

Configuration B:
{config details}

Evaluation Criteria:
- Security posture
- Cost efficiency
- Performance
- Reliability
- Operational complexity

Database Reference:
{relevant misconfigurations}

Provide:
1. Comparison matrix
2. Pros and cons for each configuration
3. Misconfiguration risk assessment for each
4. Overall recommendation with justification
5. Migration strategy if switching configurations
```

## 8. Documentation Generation

**Use Case**: Generate infrastructure documentation with security and cost considerations.

```
Generate comprehensive infrastructure documentation including misconfiguration analysis.

Infrastructure Components:
{list of AWS resources}

Include:
1. Architecture diagram description
2. Resource inventory
3. Security assessment based on misconfiguration database
4. Cost optimization opportunities
5. Operational runbooks
6. Compliance checklist

For each component, reference relevant misconfiguration entries and include:
- Current configuration status
- Alignment with best practices
- Identified gaps
- Remediation recommendations
```

## 9. Learning and Explanation

**Use Case**: Explain AWS concepts and best practices to team members.

```
Explain the following AWS misconfiguration concept in simple terms for a team member who is new to AWS.

Misconfiguration Entry:
{single entry from database}

Provide:
1. Simple explanation of what the misconfiguration is
2. Why it matters (real-world impact)
3. How to detect it
4. How to fix it
5. How to prevent it in the future
6. Related concepts they should learn
7. Common mistakes to avoid

Use analogies and examples. Assume the audience has basic cloud computing knowledge but limited AWS experience.
```

## 10. Incident Response

**Use Case**: Assist in incident response and root cause analysis.

```
An incident has occurred. Use the misconfiguration database to help with root cause analysis and remediation.

Incident Description:
{incident details}

Affected Resources:
{AWS resources involved}

Database Query:
Search for misconfigurations related to: {service_name}, {symptoms}, {error messages}

Provide:
1. Possible misconfiguration causes from database
2. Root cause analysis
3. Immediate remediation steps
4. Long-term preventive measures
5. Similar incidents to watch for
6. Documentation updates needed
```

## Example Integration Code

### Python Example

```python
import json
import openai

def analyze_with_llm(resource_config, misconfig_db):
    # Filter relevant misconfigurations
    relevant = [m for m in misconfig_db if m['service_name'] == resource_config['service']]

    prompt = f"""
    You are an AWS expert. Analyze this configuration against known misconfigurations.

    Resource Configuration:
    {json.dumps(resource_config, indent=2)}

    Known Misconfigurations for {resource_config['service']}:
    {json.dumps(relevant, indent=2)}

    Identify issues and provide recommendations.
    """

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content
```

### Usage Tips

1. **Context Window Management**: For large databases, filter to relevant entries before including in prompts
2. **Structured Output**: Request JSON or structured formats for easier parsing
3. **Incremental Analysis**: For complex infrastructure, analyze component by component
4. **Temperature Settings**: Use lower temperature (0.1-0.3) for technical analysis
5. **Few-Shot Examples**: Include 2-3 examples in your prompt for better results

## Additional Resources

- [Main Documentation](../../README.md)
- [Schema Documentation](../../docs/SCHEMA.md)
- [Python Examples](../python/README.md)
