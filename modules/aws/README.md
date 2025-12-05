# AWS Terraform Modules - CloudOps Edition

This directory contains curated Terraform modules for common AWS infrastructure patterns.

## Available Modules

### Networking
- `vpc` - AWS VPC with subnets, route tables, and gateways

### Storage
- `s3-bucket` - S3 Bucket with security best practices

### Compute
- `eks-cluster` - Amazon EKS cluster

## Usage

Reference these modules from your Terraform configuration:

```hcl
module "vpc" {
  source = "./modules/aws/vpc"
  
  vpc_name            = "my-vpc"
  cidr_block          = "10.0.0.0/16"
  availability_zones  = ["us-east-1a", "us-east-1b"]
  
  public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnet_cidrs = ["10.0.10.0/24", "10.0.11.0/24"]
  
  enable_nat_gateway = true
}
```

## Design Principles

These modules follow AWS best practices:
- Security by default
- Cost-effective configurations
- Modular and composable design
- Well-documented variables and outputs
