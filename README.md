# CloudOps - Unified Terraform IaC Toolchain

> **Zero-setup Terraform CI/CD pipeline for Azure and AWS with embedded module catalogs**

CloudOps is a comprehensive GitHub Action that delivers a complete Infrastructure-as-Code (IaC) toolchain for Terraform on Azure and AWS. It provides a zero-configuration, CI/CD-capable pipeline that aligns with best practices for cloud infrastructure management.

[![GitHub](https://img.shields.io/badge/GitHub-CloudOps-blue?logo=github)](https://github.com/Git-Cosmo/CloudOps)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 🚀 Features

- **Zero-Setup Toolchain**: Automatically installs and configures Azure CLI, AWS CLI, Terraform, and GitHub CLI
- **Multi-Cloud Support**: Deploy to Azure, AWS, or both from a single action
- **Embedded Module Catalogs**: 
  - Azure Verified Module (AVM)-style modules for Azure
  - Curated best-practice modules for AWS
- **CI/CD-Ready Workflow**: Built-in `fmt → validate → plan → apply` pipeline
- **PR Integration**: Automatic plan previews in pull request comments
- **Artifact Management**: Terraform plan files uploaded as GitHub artifacts
- **Flexible Configuration**: Simple `tf_path` input with smart working directory resolution
- **Security First**: HTTPS-only, TLS 1.2+, public access blocking by default

## 📋 Prerequisites

- GitHub repository with Terraform code
- Cloud provider credentials (Azure Service Principal or AWS Access Keys)
- GitHub Actions enabled

## 🎯 Quick Start

### Azure Deployment

```yaml
name: Azure Infrastructure

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
      
      - name: Deploy with CloudOps
        uses: Git-Cosmo/CloudOps@v1
        with:
          tf_path: ./infrastructure
          cloud_provider: azure
          terraform_operation: plan
          azure_credentials: ${{ secrets.AZURE_CREDENTIALS }}
```

### AWS Deployment

```yaml
name: AWS Infrastructure

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
      
      - name: Deploy with CloudOps
        uses: Git-Cosmo/CloudOps@v1
        with:
          tf_path: ./infrastructure
          cloud_provider: aws
          terraform_operation: plan
          aws_access_key_id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws_secret_access_key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws_region: us-east-1
```

## 📖 Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `tf_path` | ✅ Yes | - | Path to Terraform root or main configuration (file or directory) |
| `tf_working_dir` | No | (auto-resolved) | Terraform working directory |
| `cloud_provider` | No | `azure` | Cloud provider: `azure`, `aws`, or `multi` |
| `tf_version` | No | `latest` | Terraform version to install |
| `gh_cli_version` | No | `latest` | GitHub CLI version to install |
| `terraform_operation` | No | `plan` | Operation: `plan`, `apply`, or `plan-apply` |
| `azure_credentials` | No | - | Azure credentials JSON (Service Principal) |
| `aws_access_key_id` | No | - | AWS Access Key ID |
| `aws_secret_access_key` | No | - | AWS Secret Access Key |
| `aws_region` | No | `us-east-1` | AWS Region |
| `backend_config` | No | - | Backend configuration (key=value pairs, one per line) |
| `tf_vars` | No | - | Terraform variables (key=value pairs, one per line) |
| `enable_pr_comment` | No | `true` | Post plan summary as PR comment |
| `enable_artifact_upload` | No | `true` | Upload plan file as artifact |

## 📤 Outputs

| Output | Description |
|--------|-------------|
| `tf_working_dir` | Resolved Terraform working directory |
| `plan_outcome` | Outcome of terraform plan: `success`, `failure`, or `changes` |
| `apply_outcome` | Outcome of terraform apply: `success`, `failure`, or `skipped` |
| `plan_artifact_path` | Path to the generated plan file artifact |

## 🏗️ Embedded Modules

### Azure Modules (`modules/azure-avm/`)

- **virtual-network**: Azure Virtual Network with subnets
- **storage-account**: Azure Storage Account with security best practices
- **aks-cluster**: Azure Kubernetes Service (planned)

**Example Usage:**

```hcl
module "network" {
  source = "../../modules/azure-avm/virtual-network"
  
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

### AWS Modules (`modules/aws/`)

- **vpc**: AWS VPC with public/private subnets and NAT gateway
- **s3-bucket**: S3 Bucket with versioning, encryption, and lifecycle policies
- **eks-cluster**: Amazon EKS cluster (planned)

**Example Usage:**

```hcl
module "vpc" {
  source = "../../modules/aws/vpc"
  
  vpc_name           = "my-vpc"
  cidr_block         = "10.0.0.0/16"
  availability_zones = ["us-east-1a", "us-east-1b"]
  
  public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnet_cidrs = ["10.0.10.0/24", "10.0.11.0/24"]
}
```

## 🔧 Advanced Configuration

### Multi-Environment Setup

Use backend configuration for environment separation:

```yaml
- name: Deploy to Production
  uses: Git-Cosmo/CloudOps@v1
  with:
    tf_path: ./infrastructure
    cloud_provider: azure
    terraform_operation: apply
    azure_credentials: ${{ secrets.AZURE_CREDENTIALS }}
    backend_config: |
      resource_group_name=tfstate-rg
      storage_account_name=tfstateprod
      container_name=tfstate
      key=production.tfstate
```

### Custom Terraform Variables

```yaml
- name: Deploy with Custom Variables
  uses: Git-Cosmo/CloudOps@v1
  with:
    tf_path: ./infrastructure
    cloud_provider: azure
    terraform_operation: plan
    azure_credentials: ${{ secrets.AZURE_CREDENTIALS }}
    tf_vars: |
      environment=production
      instance_count=3
      enable_monitoring=true
```

### Multi-Cloud Deployment

```yaml
- name: Deploy to Multiple Clouds
  uses: Git-Cosmo/CloudOps@v1
  with:
    tf_path: ./infrastructure
    cloud_provider: multi
    terraform_operation: plan
    azure_credentials: ${{ secrets.AZURE_CREDENTIALS }}
    aws_access_key_id: ${{ secrets.AWS_ACCESS_KEY_ID }}
    aws_secret_access_key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
```

## 🔐 Security Best Practices

### Azure Credentials

Create an Azure Service Principal and store credentials as a GitHub secret:

```bash
az ad sp create-for-rbac --name "CloudOps-SP" \
  --role contributor \
  --scopes /subscriptions/{subscription-id} \
  --sdk-auth
```

Store the JSON output in GitHub Secrets as `AZURE_CREDENTIALS`.

### AWS Credentials

Create an IAM user with appropriate permissions and store access keys as GitHub secrets:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

**Recommended IAM Policy**: Use least-privilege policies based on your infrastructure needs.

### Backend State Management

Always use remote backends for state management:

**Azure:**
```hcl
backend "azurerm" {
  resource_group_name  = "tfstate-rg"
  storage_account_name = "tfstate"
  container_name       = "tfstate"
  key                  = "terraform.tfstate"
}
```

**AWS:**
```hcl
backend "s3" {
  bucket = "my-terraform-state"
  key    = "terraform.tfstate"
  region = "us-east-1"
}
```

## 🎨 Pipeline Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Install Toolchain                                        │
│    • Terraform (with version pinning)                       │
│    • Azure CLI / AWS CLI (conditional)                      │
│    • GitHub CLI                                             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Configure Cloud Providers                                │
│    • Authenticate with Azure/AWS                            │
│    • Set environment variables                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Terraform Workflow                                       │
│    • terraform init                                         │
│    • terraform fmt -check                                   │
│    • terraform validate                                     │
│    • terraform plan                                         │
│    • terraform apply (conditional)                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Artifacts & Notifications                                │
│    • Upload plan file                                       │
│    • Post PR comment with plan summary                      │
│    • Generate step summary                                  │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Repository Structure

```
CloudOps/
├── action.yml                 # GitHub Action definition
├── src/
│   └── main.py               # Python entrypoint
├── modules/
│   ├── azure-avm/            # Azure Verified Modules
│   │   ├── virtual-network/
│   │   ├── storage-account/
│   │   └── aks-cluster/
│   └── aws/                  # AWS modules
│       ├── vpc/
│       ├── s3-bucket/
│       └── eks-cluster/
├── examples/
│   ├── azure/                # Azure example configuration
│   └── aws/                  # AWS example configuration
└── .github/
    └── workflows/
        ├── example-azure.yml
        └── example-aws.yml
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Azure Verified Modules (AVM) initiative
- HashiCorp Terraform
- GitHub Actions team

## 📞 Support

For issues, questions, or contributions, please visit:
- [GitHub Issues](https://github.com/Git-Cosmo/CloudOps/issues)
- [Discussions](https://github.com/Git-Cosmo/CloudOps/discussions)

---

**Made with ❤️ by the CloudOps Team**
