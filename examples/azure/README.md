# Azure Example Configuration

This directory contains an example Terraform configuration for Azure that demonstrates the use of CloudOps embedded modules.

## What's Included

This example creates:

- **Resource Group**: A container for Azure resources
- **Virtual Network**: Using the CloudOps Azure AVM virtual-network module
  - Multiple subnets (default and app)
  - Service endpoints for Storage and KeyVault
- **Storage Account**: Using the CloudOps Azure AVM storage-account module
  - HTTPS-only with TLS 1.2+
  - Versioning enabled
  - Private access only
  - Two blob containers (data and backups)

## Prerequisites

1. Azure subscription
2. Azure Service Principal with Contributor role
3. GitHub repository with CloudOps action

## Setup

### 1. Create Azure Service Principal

```bash
az ad sp create-for-rbac --name "CloudOps-Example-SP" \
  --role contributor \
  --scopes /subscriptions/{subscription-id} \
  --sdk-auth
```

### 2. Configure Backend State Storage

Create a storage account for Terraform state:

```bash
# Create resource group
az group create --name terraform-state-rg --location eastus

# Create storage account
az storage account create \
  --name tfstateaccount \
  --resource-group terraform-state-rg \
  --location eastus \
  --sku Standard_LRS

# Create container
az storage container create \
  --name tfstate \
  --account-name tfstateaccount
```

### 3. Add GitHub Secrets

Add the following secrets to your GitHub repository:
- `AZURE_CREDENTIALS`: JSON output from the Service Principal creation

### 4. Customize Variables

Edit `variables.tf` to customize:
- Resource group name
- Location
- Virtual network settings
- Storage account name (must be globally unique)

## Deployment

The example workflow in `.github/workflows/example-azure.yml` will:

1. **On Pull Request**: Run `terraform plan` and post results as a comment
2. **On Push to Main**: Run `terraform apply` to deploy changes

## Manual Testing

You can also run Terraform commands locally:

```bash
# Initialize
terraform init \
  -backend-config="resource_group_name=terraform-state-rg" \
  -backend-config="storage_account_name=tfstateaccount" \
  -backend-config="container_name=tfstate" \
  -backend-config="key=azure-example.tfstate"

# Plan
terraform plan

# Apply
terraform apply

# Destroy
terraform destroy
```

## Module References

This example uses CloudOps embedded modules:

- `../../modules/azure-avm/virtual-network`
- `../../modules/azure-avm/storage-account`

You can customize these modules by modifying the module configuration in `main.tf`.

## Clean Up

To remove all resources:

```bash
terraform destroy
```

Or manually delete the resource group:

```bash
az group delete --name cloudops-example-rg --yes
```
