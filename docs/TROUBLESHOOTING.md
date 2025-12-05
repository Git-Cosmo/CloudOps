# CloudOps Troubleshooting Guide

This guide helps you diagnose and resolve common issues when using CloudOps for Terraform deployments.

## Table of Contents
- [Quick Diagnostics](#quick-diagnostics)
- [Authentication Issues](#authentication-issues)
- [Terraform Errors](#terraform-errors)
- [Workflow Failures](#workflow-failures)
- [State Management Issues](#state-management-issues)
- [Performance Problems](#performance-problems)
- [Debug Mode](#debug-mode)

## Quick Diagnostics

### Step 1: Check Workflow Logs

1. Go to **Actions** tab in your repository
2. Click on the failed workflow run
3. Expand failed job steps
4. Look for error messages and stack traces

### Step 2: Verify Configuration

```bash
# Check action.yml syntax
python3 -c "import yaml; yaml.safe_load(open('action.yml'))"

# Validate workflow YAML
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/your-workflow.yml'))"

# Check Terraform syntax
terraform fmt -check
terraform validate
```

### Step 3: Test Locally

```bash
# Set required environment variables
export INPUT_TF_PATH="./terraform"
export INPUT_CLOUD_PROVIDER="azure"
export INPUT_TERRAFORM_OPERATION="plan"
export GITHUB_WORKSPACE="$(pwd)"

# Run the action locally
python3 src/main.py
```

## Authentication Issues

### Azure Authentication Failures

**Symptom:**
```
Error: Failed to configure Azure credentials
az login: command failed
```

**Causes & Solutions:**

1. **Invalid Credentials JSON**
   ```bash
   # Verify JSON format
   echo $AZURE_CREDENTIALS | jq .
   
   # Should contain: clientId, clientSecret, tenantId, subscriptionId
   ```

2. **Expired Service Principal**
   ```bash
   # Check if SP exists and is active
   az ad sp show --id <clientId>
   
   # Reset credentials if needed
   az ad sp credential reset --id <clientId>
   ```

3. **Insufficient Permissions**
   ```bash
   # Verify SP has Contributor role
   az role assignment list --assignee <clientId>
   
   # Add role if missing
   az role assignment create \
     --assignee <clientId> \
     --role Contributor \
     --scope /subscriptions/<subscriptionId>
   ```

4. **Wrong Secret Name**
   ```yaml
   # Ensure secret name matches exactly
   azure_credentials: ${{ secrets.AZURE_CREDENTIALS }}
   # NOT: ${{ secrets.azure_credentials }}
   ```

### AWS Authentication Failures

**Symptom:**
```
Error: Failed to configure AWS credentials
Unable to locate credentials
```

**Causes & Solutions:**

1. **Missing Credentials**
   ```bash
   # Verify secrets are set in GitHub
   # Check: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
   ```

2. **Invalid Access Keys**
   ```bash
   # Test credentials locally
   aws sts get-caller-identity \
     --access-key-id <key> \
     --secret-access-key <secret>
   ```

3. **Incorrect Region**
   ```yaml
   # Specify correct region
   with:
     aws_region: us-east-1  # Match your resources
   ```

4. **IAM Policy Issues**
   ```bash
   # Check IAM user permissions
   aws iam get-user-policy --user-name terraform-user --policy-name TerraformPolicy
   
   # Verify attached policies
   aws iam list-attached-user-policies --user-name terraform-user
   ```

## Terraform Errors

### Plan Failures

**Symptom:**
```
Error: terraform plan failed
Invalid configuration
```

**Solutions:**

1. **Syntax Errors**
   ```bash
   # Check formatting
   terraform fmt -check -recursive
   
   # Validate configuration
   terraform validate
   ```

2. **Missing Variables**
   ```yaml
   # Add variables to workflow
   with:
     tf_vars: |
       environment=production
       instance_count=3
   ```

3. **Provider Version Conflicts**
   ```hcl
   # Pin provider versions in terraform block
   terraform {
     required_providers {
       azurerm = {
         source  = "hashicorp/azurerm"
         version = "~> 3.0"  # Be specific
       }
     }
   }
   ```

4. **Backend Configuration Issues**
   ```yaml
   # Ensure backend config is properly formatted
   backend_config: |
     resource_group_name=tfstate-rg
     storage_account_name=tfstate
     container_name=tfstate
     key=terraform.tfstate
   ```

### Apply Failures

**Symptom:**
```
Error: terraform apply failed
Resource creation failed
```

**Solutions:**

1. **Resource Already Exists**
   ```bash
   # Import existing resource
   terraform import azurerm_resource_group.example /subscriptions/.../resourceGroups/my-rg
   ```

2. **Quota Limits**
   ```bash
   # Check Azure quotas
   az vm list-usage --location eastus
   
   # Check AWS limits
   aws service-quotas list-service-quotas --service-code ec2
   ```

3. **Network Issues**
   ```bash
   # Verify connectivity
   curl https://management.azure.com/
   curl https://ec2.amazonaws.com/
   ```

4. **Dependency Errors**
   ```hcl
   # Add explicit dependencies
   resource "azurerm_subnet" "example" {
     # ...
     depends_on = [azurerm_virtual_network.example]
   }
   ```

### Validation Errors

**Symptom:**
```
Error: terraform validate failed
Reference to undeclared variable
```

**Solutions:**

1. **Missing Variable Declarations**
   ```hcl
   # Add to variables.tf
   variable "environment" {
     type        = string
     description = "Environment name"
   }
   ```

2. **Type Mismatches**
   ```hcl
   # Ensure types match
   variable "instance_count" {
     type = number  # NOT string
   }
   ```

3. **Module Path Issues**
   ```hcl
   # Use correct relative paths
   module "vpc" {
     source = "../../modules/aws/vpc"  # Check path
   }
   ```

## Workflow Failures

### Workflow Not Triggering

**Symptom:**
Workflow doesn't run when expected

**Solutions:**

1. **Path Filters**
   ```yaml
   # Check if changes match paths
   on:
     push:
       paths:
         - 'terraform/**'  # Ensure your changes are here
   ```

2. **Branch Protection**
   ```bash
   # Verify workflow permissions
   # Settings → Actions → General → Workflow permissions
   # Should have "Read and write permissions"
   ```

3. **Event Type Mismatch**
   ```yaml
   # Ensure event matches trigger
   on:
     pull_request:  # Only runs on PRs
     push:          # Add for commits to branch
   ```

### Job Failures

**Symptom:**
```
Error: Process completed with exit code 1
```

**Solutions:**

1. **Check Step Outputs**
   ```yaml
   # Add debugging steps
   - name: Debug Environment
     run: |
       echo "TF_PATH: ${{ inputs.tf_path }}"
       echo "CLOUD_PROVIDER: ${{ inputs.cloud_provider }}"
       ls -la
   ```

2. **Permissions Issues**
   ```yaml
   # Ensure proper permissions
   permissions:
     contents: read
     pull-requests: write  # Required for PR comments
     id-token: write       # Required for OIDC
   ```

3. **Timeout**
   ```yaml
   # Increase timeout
   jobs:
     terraform:
       timeout-minutes: 60  # Default is 360
   ```

### Artifact Upload Failures

**Symptom:**
```
Error: Unable to upload artifact
```

**Solutions:**

1. **File Not Found**
   ```bash
   # Verify plan file exists
   ls -la terraform/tfplan
   ```

2. **Path Configuration**
   ```yaml
   # Check artifact path matches plan location
   - uses: actions/upload-artifact@v4
     with:
       name: tfplan
       path: ${{ inputs.tf_path }}/tfplan  # Must exist
   ```

3. **Artifact Size**
   ```yaml
   # Artifacts have size limits (default 500MB)
   # Consider compressing large plans
   ```

## State Management Issues

### State Lock Errors

**Symptom:**
```
Error: Error acquiring the state lock
Lock Info: ID: xxx-xxx-xxx
```

**Solutions:**

1. **Wait for Lock Release**
   ```bash
   # Another operation may be in progress
   # Wait a few minutes and retry
   ```

2. **Force Unlock (Use with Caution)**
   ```bash
   # Only if you're sure no other operations are running
   terraform force-unlock <lock-id>
   ```

3. **Azure Storage Lease**
   ```bash
   # Check blob lease status
   az storage blob show \
     --account-name tfstate \
     --container-name tfstate \
     --name terraform.tfstate
   
   # Break lease if stuck
   az storage blob lease break \
     --account-name tfstate \
     --container-name tfstate \
     --blob-name terraform.tfstate
   ```

4. **DynamoDB Lock (AWS)**
   ```bash
   # Check lock table
   aws dynamodb get-item \
     --table-name terraform-state-lock \
     --key '{"LockID": {"S": "your-bucket/terraform.tfstate"}}'
   
   # Delete stuck lock (careful!)
   aws dynamodb delete-item \
     --table-name terraform-state-lock \
     --key '{"LockID": {"S": "your-bucket/terraform.tfstate"}}'
   ```

### State Corruption

**Symptom:**
```
Error: Failed to load state
State file corrupted
```

**Solutions:**

1. **Restore from Backup**
   ```bash
   # Azure
   az storage blob snapshot \
     --account-name tfstate \
     --container-name tfstate \
     --name terraform.tfstate
   
   # List snapshots
   az storage blob list \
     --account-name tfstate \
     --container-name tfstate \
     --include snapshots
   
   # Restore
   az storage blob copy start \
     --source-account-name tfstate \
     --source-container tfstate \
     --source-blob terraform.tfstate \
     --source-snapshot <snapshot-id> \
     --destination-container tfstate \
     --destination-blob terraform.tfstate
   ```

2. **Pull and Inspect State**
   ```bash
   terraform state pull > state.json
   cat state.json | jq .
   
   # Fix and push back
   terraform state push state.json
   ```

3. **Rebuild State**
   ```bash
   # Last resort: import resources
   terraform import azurerm_resource_group.example /subscriptions/.../resourceGroups/my-rg
   ```

### State Drift

**Symptom:**
```
Terraform detected changes made outside of Terraform
```

**Solutions:**

1. **Refresh State**
   ```bash
   terraform refresh
   ```

2. **Accept Manual Changes**
   ```bash
   # If changes are intentional
   terraform apply -refresh-only
   ```

3. **Revert Manual Changes**
   ```bash
   # Apply to restore Terraform-managed state
   terraform apply
   ```

4. **Investigate Changes**
   ```bash
   # Azure Activity Log
   az monitor activity-log list --resource-group my-rg
   
   # AWS CloudTrail
   aws cloudtrail lookup-events --lookup-attributes AttributeKey=ResourceName,AttributeValue=my-instance
   ```

## Performance Problems

### Slow Terraform Operations

**Symptom:**
Operations take unusually long

**Solutions:**

1. **Enable Parallelism**
   ```bash
   terraform apply -parallelism=20  # Default is 10
   ```

2. **Use Partial State**
   ```bash
   # Target specific resources
   terraform plan -target=module.vpc
   ```

3. **Optimize Provider Configuration**
   ```hcl
   provider "azurerm" {
     features {}
     skip_provider_registration = true  # Faster
   }
   ```

4. **Cache Plugins**
   ```bash
   # Set plugin cache directory
   export TF_PLUGIN_CACHE_DIR="$HOME/.terraform.d/plugin-cache"
   mkdir -p $TF_PLUGIN_CACHE_DIR
   ```

### Workflow Timeouts

**Symptom:**
```
Error: The job running on runner ... has exceeded the maximum execution time
```

**Solutions:**

1. **Increase Timeout**
   ```yaml
   jobs:
     terraform:
       timeout-minutes: 120  # Increase from default
   ```

2. **Split Operations**
   ```yaml
   # Separate plan and apply into different jobs
   jobs:
     plan:
       # terraform plan
     
     apply:
       needs: plan
       # terraform apply
   ```

3. **Optimize Resource Creation**
   ```hcl
   # Reduce parallelism for large deployments
   # Or split into multiple modules
   ```

## Debug Mode

### Enable Detailed Logging

**GitHub Actions Debug Logs:**
```yaml
# Add to workflow file
env:
  ACTIONS_STEP_DEBUG: true
  ACTIONS_RUNNER_DEBUG: true
```

**Terraform Debug Logs:**
```yaml
env:
  TF_LOG: DEBUG  # Options: TRACE, DEBUG, INFO, WARN, ERROR
  TF_LOG_PATH: terraform-debug.log
```

**CloudOps Debug:**
```yaml
# Python logging is already verbose
# Check job logs for detailed output
```

### Capture Logs for Support

```bash
# Download workflow logs
gh run view <run-id> --log > workflow-logs.txt

# Download Terraform logs
gh run download <run-id> --name terraform-debug-log
```

## Common Error Messages

### "Error: Failed to install Terraform"

**Solution:**
```yaml
# Specify version explicitly
with:
  tf_version: "1.5.0"  # Not "latest" if having issues
```

### "Error: No such file or directory"

**Solution:**
```yaml
# Check tf_path is correct
with:
  tf_path: examples/azure  # Ensure this directory exists
```

### "Error: working directory not found"

**Solution:**
```bash
# Verify checkout step runs first
steps:
  - uses: actions/checkout@v4  # Must be first
  - uses: Git-Cosmo/CloudOps@v1
```

### "Error: Module not found"

**Solution:**
```hcl
# Use correct module source
module "vpc" {
  source = "../../modules/aws/vpc"  # Check relative path
  # Or use Git source
  source = "git::https://github.com/Git-Cosmo/CloudOps.git//modules/aws/vpc"
}
```

## Getting Help

### Self-Service Resources

1. **Documentation**
   - [README](../README.md)
   - [Architecture Guide](../ARCHITECTURE.md)
   - [Quick Start](../QUICKSTART.md)

2. **Workflow Logs**
   - Always check full workflow logs first
   - Look for stack traces and error codes

3. **Community**
   - Search [GitHub Issues](https://github.com/Git-Cosmo/CloudOps/issues)
   - Check [Discussions](https://github.com/Git-Cosmo/CloudOps/discussions)

### Creating Support Tickets

Include:
1. **Workflow run URL**
2. **Error message (full text)**
3. **Relevant workflow YAML**
4. **Terraform version**
5. **Cloud provider**
6. **Steps to reproduce**

### Emergency Contacts

**Critical Production Issues:**
- Internal escalation to Platform Team
- GitHub Enterprise Support (if applicable)
- Cloud Provider Support

---

**Document Version:** 1.0  
**Last Updated:** 2025-12-05  
**Maintainer:** Platform Team
