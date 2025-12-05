# Security Best Practices for CloudOps

This document outlines security best practices for using CloudOps in production environments.

## Table of Contents
- [Credential Management](#credential-management)
- [Access Control](#access-control)
- [Network Security](#network-security)
- [State File Security](#state-file-security)
- [Secrets Scanning](#secrets-scanning)
- [Audit and Compliance](#audit-and-compliance)
- [Incident Response](#incident-response)

## Credential Management

### Service Principal / IAM Best Practices

**Azure Service Principal:**

1. **Use Least Privilege**
   ```bash
   # Create custom role instead of Contributor
   az role definition create --role-definition '{
     "Name": "Terraform Operator",
     "Description": "Can manage Terraform resources",
     "Actions": [
       "Microsoft.Resources/deployments/*",
       "Microsoft.Resources/subscriptions/resourceGroups/*",
       "Microsoft.Network/*",
       "Microsoft.Compute/virtualMachines/*"
     ],
     "NotActions": [
       "Microsoft.Authorization/*/Delete",
       "Microsoft.Authorization/*/Write"
     ],
     "AssignableScopes": ["/subscriptions/{subscription-id}"]
   }'
   ```

2. **Separate Service Principals per Environment**
   ```bash
   # Development
   az ad sp create-for-rbac --name "CloudOps-Dev-SP" \
     --role "Terraform Operator" \
     --scopes /subscriptions/{dev-subscription-id}
   
   # Production
   az ad sp create-for-rbac --name "CloudOps-Prod-SP" \
     --role "Terraform Operator" \
     --scopes /subscriptions/{prod-subscription-id}
   ```

3. **Enable Credential Expiration**
   ```bash
   # Set credential expiry (1 year)
   az ad sp credential reset \
     --id <app-id> \
     --years 1
   ```

**AWS IAM Best Practices:**

1. **Use IAM Policies with Conditions**
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "ec2:*",
           "s3:*",
           "dynamodb:*"
         ],
         "Resource": "*",
         "Condition": {
           "StringEquals": {
             "aws:RequestedRegion": "us-east-1",
             "aws:PrincipalTag/Environment": "production"
           }
         }
       }
     ]
   }
   ```

2. **Use Resource Tags for Access Control**
   ```json
   {
     "Effect": "Allow",
     "Action": "ec2:*",
     "Resource": "*",
     "Condition": {
       "StringEquals": {
         "ec2:ResourceTag/ManagedBy": "Terraform"
       }
     }
   }
   ```

3. **Enable MFA for Sensitive Operations**
   ```json
   {
     "Effect": "Deny",
     "Action": "ec2:TerminateInstances",
     "Resource": "*",
     "Condition": {
       "BoolIfExists": {
         "aws:MultiFactorAuthPresent": "false"
       }
     }
   }
   ```

### GitHub Secrets Management

1. **Use Environment Secrets**
   ```yaml
   # More restrictive than repository secrets
   jobs:
     deploy:
       environment: production  # Requires approval
       secrets:
         azure_credentials: ${{ secrets.AZURE_CREDENTIALS }}
   ```

2. **Never Log Secrets**
   ```python
   # Good - secrets never appear in logs
   logger.info("Configuring Azure credentials...")
   
   # Bad - DO NOT DO THIS
   logger.info(f"Using credentials: {credentials}")
   ```

3. **Rotate Secrets Regularly**
   - Development: Every 180 days
   - Staging: Every 90 days
   - Production: Every 60 days

4. **Use GitHub Secret Scanning**
   ```yaml
   # Enable in repository settings
   Settings → Security → Code security and analysis
   → Secret scanning: Enable
   ```

### OIDC Authentication (Recommended)

**Azure:**
```yaml
permissions:
  id-token: write  # Required for OIDC
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: azure/login@v1
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
```

**AWS:**
```yaml
permissions:
  id-token: write  # Required for OIDC
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsRole
          aws-region: us-east-1
```

## Access Control

### Repository Access

1. **Team-Based Access Control**
   ```
   Infrastructure-Admin: Admin
   DevOps-Team: Write
   Developers: Read
   ```

2. **Branch Protection Rules**
   ```yaml
   # .github/branch-protection.yml
   main:
     required_pull_request_reviews:
       required_approving_review_count: 2
       dismiss_stale_reviews: true
       require_code_owner_reviews: true
     required_status_checks:
       strict: true
       contexts:
         - "ci/lint"
         - "ci/test"
         - "ci/security-scan"
     enforce_admins: true
     required_linear_history: true
   ```

3. **CODEOWNERS File**
   ```
   # .github/CODEOWNERS
   # Infrastructure team must approve all changes
   * @org/infrastructure-team
   
   # Production requires platform team approval
   environments/production/ @org/platform-team
   
   # Workflows require security team review
   .github/workflows/ @org/security-team
   ```

### GitHub Environments

**Production Environment:**
```yaml
# Settings → Environments → production
Protection rules:
  - Required reviewers: 2 from @org/infrastructure-team
  - Wait timer: 30 minutes
  - Deployment branches: main only
  - Environment secrets: Production credentials
```

## Network Security

### Terraform Configuration

**Azure:**
```hcl
# Enable HTTPS only
resource "azurerm_storage_account" "example" {
  https_traffic_only_enabled = true
  min_tls_version            = "TLS1_2"

  # Disable public access
  allow_nested_items_to_be_public = false
  
  # Enable firewall
  network_rules {
    default_action = "Deny"
    ip_rules       = ["1.2.3.4/32"]  # Only allow specific IPs
    virtual_network_subnet_ids = [azurerm_subnet.trusted.id]
  }
}
```

**AWS:**
```hcl
# Block all public access
resource "aws_s3_bucket_public_access_block" "example" {
  bucket = aws_s3_bucket.example.id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Enable encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "example" {
  bucket = aws_s3_bucket.example.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
```

### VPC Security

**AWS Security Groups:**
```hcl
resource "aws_security_group" "restrictive" {
  name        = "restrictive-sg"
  description = "Minimal access security group"
  
  # No ingress rules by default
  
  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS only"
  }
}
```

**Azure Network Security Groups:**
```hcl
resource "azurerm_network_security_group" "restrictive" {
  name                = "restrictive-nsg"
  location            = azurerm_resource_group.example.location
  resource_group_name = azurerm_resource_group.example.name
  
  security_rule {
    name                       = "DenyAllInbound"
    priority                   = 4096
    direction                  = "Inbound"
    access                     = "Deny"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
}
```

## State File Security

### Backend Encryption

**Azure:**
```hcl
terraform {
  backend "azurerm" {
    resource_group_name  = "tfstate-rg"
    storage_account_name = "tfstatesecure"
    container_name       = "tfstate"
    key                  = "production.tfstate"
    
    # Enable Azure AD authentication
    use_azuread_auth = true
    
    # Enable encryption (always enabled for Azure Storage)
  }
}

# Configure storage account encryption
resource "azurerm_storage_account" "tfstate" {
  name                     = "tfstatesecure"
  resource_group_name      = azurerm_resource_group.tfstate.name
  location                 = azurerm_resource_group.tfstate.location
  account_tier             = "Standard"
  account_replication_type = "GRS"
  
  # Enable encryption with customer-managed keys
  identity {
    type = "SystemAssigned"
  }
  
  encryption {
    key_vault_key_id = azurerm_key_vault_key.tfstate.id
  }
}
```

**AWS:**
```hcl
terraform {
  backend "s3" {
    bucket         = "terraform-state-secure"
    key            = "production.tfstate"
    region         = "us-east-1"
    
    # Enable encryption
    encrypt        = true
    kms_key_id     = "arn:aws:kms:us-east-1:123456789012:key/..."
    
    # Enable locking
    dynamodb_table = "terraform-state-lock"
  }
}

# Configure S3 bucket security
resource "aws_s3_bucket" "tfstate" {
  bucket = "terraform-state-secure"
  
  versioning {
    enabled = true
  }
  
  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm     = "aws:kms"
        kms_master_key_id = aws_kms_key.tfstate.arn
      }
    }
  }
  
  lifecycle_rule {
    enabled = true
    
    noncurrent_version_expiration {
      days = 90
    }
  }
}
```

### State File Access Control

**Azure:**
```bash
# Use Azure RBAC for state access
az role assignment create \
  --role "Storage Blob Data Contributor" \
  --assignee <service-principal-id> \
  --scope /subscriptions/.../resourceGroups/tfstate-rg/providers/Microsoft.Storage/storageAccounts/tfstate
```

**AWS:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": [
        "arn:aws:s3:::terraform-state-secure",
        "arn:aws:s3:::terraform-state-secure/*"
      ],
      "Condition": {
        "StringEquals": {
          "s3:x-amz-server-side-encryption": "aws:kms"
        }
      }
    }
  ]
}
```

## Secrets Scanning

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: detect-private-key
      - id: detect-aws-credentials
      
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
```

### CI/CD Secret Scanning

```yaml
# Add to .github/workflows/ci.yml
- name: Scan for secrets
  uses: trufflesecurity/trufflehog@main
  with:
    path: ./
    base: ${{ github.event.repository.default_branch }}
    head: HEAD
```

### Response to Exposed Secrets

1. **Immediate Actions:**
   - Revoke compromised credentials
   - Remove from Git history
   - Rotate all related secrets
   - Audit access logs

2. **Git History Cleanup:**
   ```bash
   # Use BFG Repo-Cleaner or git-filter-repo
   git filter-repo --invert-paths --path path/to/secret
   ```

## Audit and Compliance

### Logging Requirements

**GitHub Actions:**
```yaml
# Enable verbose logging for audit
env:
  ACTIONS_STEP_DEBUG: true
```

**Azure Activity Log:**
```hcl
resource "azurerm_monitor_log_profile" "audit" {
  name = "audit-profile"
  
  categories = [
    "Write",
    "Delete",
    "Action"
  ]
  
  locations = ["global", "eastus"]
  
  storage_account_id = azurerm_storage_account.audit.id
  
  retention_policy {
    enabled = true
    days    = 2555  # 7 years for compliance
  }
}
```

**AWS CloudTrail:**
```hcl
resource "aws_cloudtrail" "audit" {
  name                          = "audit-trail"
  s3_bucket_name                = aws_s3_bucket.audit.id
  include_global_service_events = true
  is_multi_region_trail         = true
  enable_log_file_validation    = true
  
  event_selector {
    read_write_type           = "All"
    include_management_events = true
    
    data_resource {
      type   = "AWS::S3::Object"
      values = ["arn:aws:s3:::*/"]
    }
  }
}
```

### Compliance Standards

**SOC 2:**
- All changes tracked in version control
- Approval workflows for production
- Audit logs retained for required period
- Access reviews conducted quarterly

**HIPAA:**
- Encryption at rest and in transit
- Access logging enabled
- PHI data properly tagged and isolated
- Regular security assessments

**PCI DSS:**
- Network segmentation implemented
- Change management process documented
- Vulnerability scanning enabled
- Access control properly configured

### Policy Enforcement

**Azure Policy:**
```hcl
resource "azurerm_policy_definition" "require_tags" {
  name         = "require-tags"
  policy_type  = "Custom"
  mode         = "All"
  display_name = "Require specific tags"
  
  policy_rule = jsonencode({
    if = {
      allOf = [
        {
          field  = "type"
          equals = "Microsoft.Resources/subscriptions/resourceGroups"
        },
        {
          field    = "tags['ManagedBy']"
          notEquals = "Terraform"
        }
      ]
    }
    then = {
      effect = "deny"
    }
  })
}
```

## Incident Response

### Security Incident Playbook

**1. Detection**
```yaml
# Alerts configured for:
- Unauthorized access attempts
- Unusual deployment patterns
- Failed authentication attempts
- State file modifications
```

**2. Containment**
```bash
# Immediately revoke compromised credentials
az ad sp credential reset --id <app-id>
aws iam delete-access-key --access-key-id <key-id>

# Lock down affected resources
terraform apply -target=resource.security_group
```

**3. Investigation**
```bash
# Review audit logs
az monitor activity-log list --resource-group <rg>
aws cloudtrail lookup-events --start-time <time>

# Check state file history
terraform state pull > current.tfstate
```

**4. Recovery**
```bash
# Restore from known-good state
terraform state push backup.tfstate

# Re-apply security controls
terraform apply
```

**5. Post-Incident**
- Document incident
- Update security controls
- Conduct post-mortem
- Update runbooks

### Contact Information

**Security Team:** security@company.com  
**On-Call Rotation:** PagerDuty / OpsGenie  
**Escalation:** CTO / CISO

## Security Checklist

Before deploying to production, verify:

- [ ] Service principals use least privilege
- [ ] Secrets are stored in GitHub Secrets / Key Vault
- [ ] OIDC authentication configured (if supported)
- [ ] Branch protection rules enabled
- [ ] Required reviewers configured
- [ ] State file encryption enabled
- [ ] State file access restricted
- [ ] Network security groups configured
- [ ] Public access blocked
- [ ] TLS/HTTPS enforced
- [ ] Audit logging enabled
- [ ] Secret scanning enabled
- [ ] Pre-commit hooks installed
- [ ] Backup procedures documented
- [ ] Incident response plan reviewed

---

**Document Version:** 1.0  
**Last Updated:** 2025-12-05  
**Maintainer:** Security Team
