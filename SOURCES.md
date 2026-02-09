# AWS Source Catalog for Recommendation Library

A curated catalog of authoritative sources for discovering and mining AWS misconfiguration recommendations. Use this as a living reference for systematically growing the library — especially in underrepresented categories.

**Current library distribution:** operations (209), cost (80), performance (33), security (19), reliability (12)

---

## 1. AWS Official RSS Feeds

Subscribable feeds for staying current with AWS changes, new features, and best practice updates.

| Feed | URL | Categories |
|---|---|---|
| AWS Security Blog | `https://aws.amazon.com/blogs/security/feed/` | security |
| AWS Architecture Blog | `https://aws.amazon.com/blogs/architecture/feed/` | reliability, performance, operations |
| AWS News Blog | `https://aws.amazon.com/blogs/aws/feed/` | all |
| AWS What's New | `https://aws.amazon.com/about-aws/whats-new/recent/feed/` | all |
| AWS Cost Management Blog | `https://aws.amazon.com/blogs/aws-cost-management/feed/` | cost |
| AWS DevOps Blog | `https://aws.amazon.com/blogs/devops/feed/` | operations |
| AWS Database Blog | `https://aws.amazon.com/blogs/database/feed/` | performance, reliability, security |
| AWS Networking Blog | `https://aws.amazon.com/blogs/networking-and-content-delivery/feed/` | performance, operations |
| AWS Compute Blog | `https://aws.amazon.com/blogs/compute/feed/` | performance, cost, operations |
| AWS Storage Blog | `https://aws.amazon.com/blogs/storage/feed/` | cost, reliability |
| AWS Containers Blog | `https://aws.amazon.com/blogs/containers/feed/` | operations, security |
| Well-Architected Framework RSS | `https://docs.aws.amazon.com/wellarchitected/latest/framework/wellarchitected-framework.rss` | all |
| AWS Service Health Dashboard | `https://status.aws.amazon.com/rss/all.rss` | reliability |

> **See also:** Community-maintained OPML collection of all AWS RSS feeds: https://github.com/HamadaKoji/aws-public-rss-feeds

---

## 2. AWS Authoritative Documentation (Primary Mining Sources)

Structured, enumerable sources where each check, rule, or control can map directly to a recommendation. These are the highest-value sources for systematic extraction.

| Source | URL | Est. Checks | Categories |
|---|---|---|---|
| **AWS Security Hub Controls** | https://docs.aws.amazon.com/securityhub/latest/userguide/securityhub-controls-reference.html | 400+ | security |
| **AWS Config Managed Rules** | https://docs.aws.amazon.com/config/latest/developerguide/managed-rules-by-aws-config.html | 200+ | security, operations |
| **AWS Trusted Advisor Checks** | https://docs.aws.amazon.com/awssupport/latest/user/trusted-advisor-check-reference.html | 482 | cost, security, performance, reliability, operations |
| **AWS Control Tower Controls** | https://docs.aws.amazon.com/controltower/latest/controlreference/controls-reference.html | 750+ | security, operations |
| **CIS AWS Foundations Benchmark** | https://www.cisecurity.org/benchmark/amazon_web_services | 43+ | security |
| **Well-Architected Framework** | https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html | — | all |
| **AWS Security Reference Architecture** | https://docs.aws.amazon.com/prescriptive-guidance/latest/security-reference-architecture/ | — | security |
| **CUR Column Dictionary** | https://docs.aws.amazon.com/cur/latest/userguide/table-dictionary-cor-columns.html | — | cost |

---

## 3. Open-Source Security Tool Rule Sets

Tools with publicly available rule definitions that can be cross-referenced to find gaps in our library.

| Tool | Rules URL / Repo | Est. Rules | Focus |
|---|---|---|---|
| **Prowler** | https://github.com/prowler-cloud/prowler | 300+ | security, compliance |
| **Checkov** | https://www.checkov.io/ | 1000+ (177 AWS) | IaC security |
| **ScoutSuite** | https://github.com/nccgroup/ScoutSuite | varies | security audit |
| **KICS** | https://github.com/Checkmarx/kics | 1900+ | IaC security |
| **Trivy** | https://github.com/aquasecurity/trivy | varies | IaC + vulnerability |
| **CloudSploit** | https://github.com/aquasecurity/cloudsploit | varies | misconfiguration |
| **CloudMapper** | https://github.com/duo-labs/cloudmapper | varies | network, IAM, unused resources |
| **Steampipe AWS Compliance** | https://hub.steampipe.io/mods/turbot/aws_compliance | 500+ | compliance benchmarks |

---

## 4. Newsletters and Aggregators

Curated content for discovering emerging patterns and new misconfiguration types.

| Source | URL | Frequency | Focus |
|---|---|---|---|
| **aws-news.com** | https://aws-news.com/ | continuous | AWS news aggregation |
| **Last Week in AWS** | https://www.lastweekinaws.com/ | weekly | AWS news + cost |
| **CloudSecList** | https://cloudseclist.com/ | weekly | cloud security |
| **tl;dr sec** | https://tldrsec.com/ | weekly | appsec + cloud security |
| **Cloud Security Newsletter** | https://www.cloudsecuritynewsletter.com/ | weekly | cloud security |
| **Sysdig AWS Feed** | https://sysdig.com/company/sysdig-rss-feeds/ | continuous | container + cloud security |

---

## 5. AWS Whitepapers and Guides

Deep-dive documents for batch recommendation extraction, organized by Well-Architected pillar.

| Document | URL | Categories |
|---|---|---|
| Cost Optimization Pillar | https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html | cost |
| Security Pillar | https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html | security |
| Reliability Pillar | https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/welcome.html | reliability |
| Performance Efficiency Pillar | https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/welcome.html | performance |
| Operational Excellence Pillar | https://docs.aws.amazon.com/wellarchitected/latest/operational-excellence-pillar/welcome.html | operations |
| Sustainability Pillar | https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/welcome.html | operations |
| Organizing Your AWS Environment | https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/ | security, operations |
| AWS Pricing / Cost Optimization | https://docs.aws.amazon.com/whitepapers/latest/how-aws-pricing-works/aws-cost-optimization.html | cost |

---

## 6. Vulnerability and Advisory Sources

| Source | URL | Use |
|---|---|---|
| AWS Security Bulletins | https://aws.amazon.com/security/security-bulletins/ | AWS-specific vulnerabilities |
| Amazon Linux Security Advisories | https://alas.aws.amazon.com/ | Linux AMI vulnerabilities |
| NVD (NIST) | https://nvd.nist.gov/ | Cloud-relevant CVEs |
| GuardDuty Finding Types | https://docs.aws.amazon.com/guardduty/latest/ug/guardduty_finding-types-active.html | Threat detection patterns |

---

## 7. Community and Curated Lists

| Source | URL | Description |
|---|---|---|
| Awesome AWS Security | https://github.com/coffeewithayman/awesome-aws-security | Curated tools + resources |
| AWS Security Tools | https://github.com/0xVariable/AWS-Security-Tools | Tool collection |
| ASecure.Cloud | https://asecure.cloud/tools/ | Cloud security resources |
| AWS Security Best Practices | https://aws.github.io/aws-security-services-best-practices/ | Per-service guides (Macie, GuardDuty, etc.) |

---

## Priority Gap Analysis

Based on the current library distribution, the highest-value sources to mine next are:

1. **Security (most underrepresented at 19):** Security Hub Controls (400+), CIS Benchmarks (43+), Prowler (300+)
2. **Reliability (12):** Well-Architected Reliability Pillar, Trusted Advisor fault tolerance checks
3. **Performance (33):** Trusted Advisor performance checks, Compute Optimizer guidance
4. **Cost (80):** Trusted Advisor cost checks (largest section), CUR documentation
5. **Operations (209):** Already well-covered; focus on new services only
