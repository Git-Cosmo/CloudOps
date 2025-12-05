terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    # Backend configuration provided via workflow
  }
}

provider "aws" {
  region = var.aws_region
}

# Use CloudOps AWS module for VPC
module "vpc" {
  source = "../../modules/aws/vpc"
  
  vpc_name           = var.vpc_name
  cidr_block         = var.vpc_cidr_block
  availability_zones = var.availability_zones
  
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
  
  enable_nat_gateway = var.enable_nat_gateway
  single_nat_gateway = var.single_nat_gateway
  
  tags = var.common_tags
}

# Use CloudOps AWS module for S3 bucket
module "data_bucket" {
  source = "../../modules/aws/s3-bucket"
  
  bucket_name           = var.data_bucket_name
  enable_versioning     = true
  block_public_access   = true
  sse_algorithm         = "AES256"
  
  lifecycle_rules = [
    {
      id              = "archive-old-data"
      enabled         = true
      expiration_days = null
      transitions = [
        {
          days          = 90
          storage_class = "GLACIER"
        }
      ]
    }
  ]
  
  tags = var.common_tags
}
