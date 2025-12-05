# CloudOps Quick Start Guide

Get started with CloudOps in 5 minutes or less!

## Prerequisites

- GitHub repository with Terraform code
- Cloud provider account (Azure or AWS)
- GitHub Actions enabled on your repository

## Quick Setup

### Option 1: Azure Deployment

#### Step 1: Set up Azure Credentials

```bash
# Create a service principal
az ad sp create-for-rbac \
  --name "CloudOps-GitHub-SP" \
  --role Contributor \
  --scopes /subscriptions/{subscription-id} \
  --sdk-auth
```

Copy the JSON output.

#### Step 2: Add GitHub Secret

1. Go to your repository → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `AZURE_CREDENTIALS`
4. Value: Paste the JSON from Step 1

#### Step 3: Create Workflow

Create `.github/workflows/terraform.yml`:

```yaml
name: Terraform Azure

on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read
  pull-requests: write

jobs:
  terraform:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Terraform Pipeline
        uses: Git-Cosmo/CloudOps@v1
        with:
          tf_path: ./terraform
          cloud_provider: azure
          terraform_operation: plan
          azure_credentials: ${{ secrets.AZURE_CREDENTIALS }}
```

#### Step 4: Push and Watch

```bash
git add .github/workflows/terraform.yml
git commit -m "Add CloudOps workflow"
git push
```

🎉 Your Terraform pipeline is now running!

---

### Option 2: AWS Deployment

#### Step 1: Create IAM User

1. Go to AWS Console → IAM → Users
2. Create new user with programmatic access
3. Attach appropriate policies (e.g., `AdministratorAccess` for testing)
4. Save Access Key ID and Secret Access Key

#### Step 2: Add GitHub Secrets

Add these secrets to your repository:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

#### Step 3: Create Workflow

Create `.github/workflows/terraform.yml`:

```yaml
name: Terraform AWS

on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read
  pull-requests: write

jobs:
  terraform:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Terraform Pipeline
        uses: Git-Cosmo/CloudOps@v1
        with:
          tf_path: ./terraform
          cloud_provider: aws
          terraform_operation: plan
          aws_access_key_id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws_secret_access_key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws_region: us-east-1
```

#### Step 4: Push and Watch

```bash
git add .github/workflows/terraform.yml
git commit -m "Add CloudOps workflow"
git push
```

🎉 Your Terraform pipeline is now running!

---

## What Happens Next?

### On Pull Requests

CloudOps will:
1. ✅ Format your Terraform code
2. ✅ Validate the configuration
3. ✅ Generate a plan
4. 💬 Post the plan as a PR comment
5. 📦 Upload the plan as an artifact

### On Main Branch

CloudOps can:
1. ✅ Run the same checks as PRs
2. 🚀 Apply changes (if you set `terraform_operation: apply`)

---

## Using Embedded Modules

CloudOps includes pre-built modules for common patterns.

### Azure Virtual Network Example

```hcl
module "network" {
  source = "git::https://github.com/Git-Cosmo/CloudOps.git//modules/azure-avm/virtual-network"
  
  resource_group_name = "my-rg"
  location            = "eastus"
  vnet_name          = "my-vnet"
  address_space      = ["10.0.0.0/16"]
  
  subnets = {
    default = {
      address_prefix = "10.0.1.0/24"
    }
  }
}
```

### AWS VPC Example

```hcl
module "vpc" {
  source = "git::https://github.com/Git-Cosmo/CloudOps.git//modules/aws/vpc"
  
  vpc_name           = "my-vpc"
  cidr_block         = "10.0.0.0/16"
  availability_zones = ["us-east-1a", "us-east-1b"]
  
  public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnet_cidrs = ["10.0.10.0/24", "10.0.11.0/24"]
}
```

---

## Common Configurations

### Plan on PR, Apply on Merge

```yaml
jobs:
  plan:
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: Git-Cosmo/CloudOps@v1
        with:
          tf_path: ./terraform
          cloud_provider: azure
          terraform_operation: plan
          azure_credentials: ${{ secrets.AZURE_CREDENTIALS }}
  
  apply:
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4
      - uses: Git-Cosmo/CloudOps@v1
        with:
          tf_path: ./terraform
          cloud_provider: azure
          terraform_operation: apply
          azure_credentials: ${{ secrets.AZURE_CREDENTIALS }}
```

### With Backend Configuration

```yaml
- uses: Git-Cosmo/CloudOps@v1
  with:
    tf_path: ./terraform
    cloud_provider: azure
    terraform_operation: plan
    azure_credentials: ${{ secrets.AZURE_CREDENTIALS }}
    backend_config: |
      resource_group_name=tfstate-rg
      storage_account_name=tfstate
      container_name=tfstate
      key=prod.tfstate
```

### With Custom Variables

```yaml
- uses: Git-Cosmo/CloudOps@v1
  with:
    tf_path: ./terraform
    cloud_provider: azure
    terraform_operation: plan
    azure_credentials: ${{ secrets.AZURE_CREDENTIALS }}
    tf_vars: |
      environment=production
      instance_count=3
```

---

## Troubleshooting

### "Authentication failed"

**Azure**: Verify your service principal has the correct permissions and the JSON is properly formatted.

**AWS**: Verify your access keys are correct and the IAM user has necessary permissions.

### "terraform: command not found"

This shouldn't happen! CloudOps installs Terraform automatically. If you see this, please open an issue.

### "Plan failed"

Check your Terraform syntax:
```bash
terraform validate
```

Review the plan output in the workflow logs for specific errors.

---

## Next Steps

- 📖 Read the [full README](README.md) for all features
- 🏗️ Check out [example configurations](examples/)
- 🔧 Explore [embedded modules](modules/)
- 💬 Join [discussions](https://github.com/Git-Cosmo/CloudOps/discussions)

---

## Need Help?

- 📖 [Documentation](README.md)
- 🐛 [Report an issue](https://github.com/Git-Cosmo/CloudOps/issues)
- 💬 [Ask a question](https://github.com/Git-Cosmo/CloudOps/discussions)

---

**Happy Infrastructure as Code! 🚀**
