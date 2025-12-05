# Enterprise Onboarding Guide

This guide provides comprehensive instructions for adopting CloudOps in an enterprise environment with multiple teams, environments, and compliance requirements.

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Multi-Environment Setup](#multi-environment-setup)
- [RBAC Configuration](#rbac-configuration)
- [Secrets Management](#secrets-management)
- [Compliance & Audit](#compliance--audit)
- [State Management](#state-management)
- [Monitoring & Alerting](#monitoring--alerting)
- [Troubleshooting](#troubleshooting)

## Overview

CloudOps is designed to support enterprise-scale infrastructure management with:
- Multi-environment deployments (dev, staging, production)
- Role-based access control (RBAC)
- Audit logging and compliance
- Team collaboration workflows
- Centralized state management
- Security best practices

## Prerequisites

### Organizational Setup
1. **GitHub Organization**
   - GitHub Enterprise account (recommended)
   - Organization-level secrets for shared credentials
   - Team-based repository access

2. **Cloud Provider Accounts**
   - Separate accounts/subscriptions per environment
   - Service principals/IAM roles with least privilege
   - Cost management and budget alerts configured

3. **Infrastructure Requirements**
   - Remote state backend (Azure Storage or S3)
   - Networking and connectivity
   - Security and compliance tools

## Multi-Environment Setup

### Recommended Directory Structure

```
infrastructure/
├── .github/
│   └── workflows/
│       ├── dev-deploy.yml
│       ├── staging-deploy.yml
│       └── production-deploy.yml
├── environments/
│   ├── dev/
│   ├── staging/
│   └── production/
└── modules/
    ├── networking/
    ├── compute/
    └── database/
```

### Workflow Configuration per Environment

**Production Environment:**
```yaml
name: Deploy to Production

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pull-requests: write

jobs:
  plan:
    uses: ./.github/workflows/reusable-terraform.yml
    with:
      cloud_provider: azure
      tf_path: environments/production
      terraform_operation: plan
      artifact_name: production-plan
    secrets:
      azure_credentials: ${{ secrets.AZURE_CREDENTIALS_PROD }}
  
  approve:
    needs: plan
    runs-on: ubuntu-latest
    environment: production-approval
    steps:
      - name: Approval Gate
        run: echo "Approved for production deployment"
  
  apply:
    needs: approve
    uses: ./.github/workflows/reusable-terraform.yml
    with:
      cloud_provider: azure
      tf_path: environments/production
      terraform_operation: apply
      environment: production
    secrets:
      azure_credentials: ${{ secrets.AZURE_CREDENTIALS_PROD }}
```

## RBAC Configuration

### GitHub Environments

Create environments with protection rules:

**Production:**
- Required reviewers: 2 Infrastructure Team members
- Wait timer: 30 minutes (optional)
- Deployment branches: main only

### Azure RBAC

**Production (Least Privilege):**
```bash
az ad sp create-for-rbac \
  --name "CloudOps-Prod-SP" \
  --role "Terraform Deployment" \
  --scopes /subscriptions/{prod-subscription-id} \
  --sdk-auth
```

## Secrets Management

### GitHub Secrets Organization

**Repository-level Secrets:**
- `AZURE_CREDENTIALS_DEV`
- `AZURE_CREDENTIALS_STAGING`
- `AZURE_CREDENTIALS_PROD`
- `AWS_ACCESS_KEY_ID_PROD`
- `AWS_SECRET_ACCESS_KEY_PROD`

### Secret Rotation Policy

**Frequency:**
- Development: Every 180 days
- Staging: Every 90 days
- Production: Every 60 days

## Compliance & Audit

### Audit Logging

**GitHub Audit Log:**
- Enable organization audit log
- Export to SIEM (Splunk, ELK, etc.)
- Monitor workflow executions
- Track secret access

**Azure Activity Log:**
```hcl
resource "azurerm_monitor_diagnostic_setting" "audit" {
  name                       = "audit-logs"
  target_resource_id         = azurerm_resource_group.main.id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id

  log {
    category = "Administrative"
    enabled  = true
  }
}
```

## State Management

### Backend Configuration

**Azure:**
```hcl
terraform {
  backend "azurerm" {
    resource_group_name  = "tfstate-rg"
    storage_account_name = "tfstateenterprise"
    container_name       = "tfstate"
    key                  = "production/network.tfstate"
    use_azuread_auth     = true
  }
}
```

**AWS:**
```hcl
terraform {
  backend "s3" {
    bucket         = "terraform-state-enterprise"
    key            = "production/network.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-state-lock"
    encrypt        = true
  }
}
```

## Monitoring & Alerting

### GitHub Actions Notifications

**Slack Integration:**
```yaml
- name: Notify Slack on failure
  if: failure()
  uses: slackapi/slack-github-action@v1
  with:
    channel-id: 'infrastructure-alerts'
    slack-message: |
      Terraform deployment failed
      Run: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}
  env:
    SLACK_BOT_TOKEN: ${{ secrets.SLACK_BOT_TOKEN }}
```

## Troubleshooting

### Common Issues

**Issue: Authentication Failures**
```
Solution:
1. Verify secret names match workflow
2. Check service principal/IAM permissions
3. Ensure credentials haven't expired
```

**Issue: State Lock Errors**
```
Solution:
1. Check for stuck workflows
2. Manually release lock: terraform force-unlock <lock-id>
3. Verify DynamoDB table exists (AWS)
```

### Debug Mode

Enable detailed logging:
```yaml
env:
  ACTIONS_STEP_DEBUG: true
  TF_LOG: DEBUG
```

## Success Metrics

### KPIs to Track

1. **Deployment Frequency** - Target: Weekly in production
2. **Lead Time for Changes** - Target: < 1 hour for urgent changes
3. **Mean Time to Recovery (MTTR)** - Target: < 1 hour
4. **Change Failure Rate** - Target: < 5%

## Conclusion

This guide provides a foundation for enterprise adoption of CloudOps. Customize based on your organization's specific requirements.

---

**Document Version:** 1.0  
**Last Updated:** 2025-12-05  
**Maintainer:** Platform Team
