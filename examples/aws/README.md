# AWS Example Configuration

This directory contains an example Terraform configuration for AWS that demonstrates the use of CloudOps embedded modules.

## What's Included

This example creates:

- **VPC**: Using the CloudOps AWS vpc module
  - Public and private subnets across multiple AZs
  - Internet Gateway for public subnets
  - NAT Gateway for private subnet internet access
  - Route tables configured appropriately
- **S3 Bucket**: Using the CloudOps AWS s3-bucket module
  - Versioning enabled
  - Server-side encryption (AES256)
  - Public access blocked
  - Lifecycle policy (archive to Glacier after 90 days)

## Prerequisites

1. AWS account
2. IAM user with appropriate permissions
3. GitHub repository with CloudOps action

## Setup

### 1. Create IAM User

Create an IAM user with programmatic access and attach policies:

**Minimum Required Policies:**
- `AmazonVPCFullAccess`
- `AmazonS3FullAccess`

Or create a custom policy with least-privilege access based on your needs.

### 2. Configure Backend State Storage

Create an S3 bucket for Terraform state:

```bash
# Create bucket
aws s3 mb s3://my-terraform-state-bucket --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket my-terraform-state-bucket \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket my-terraform-state-bucket \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'
```

### 3. Add GitHub Secrets

Add the following secrets to your GitHub repository:
- `AWS_ACCESS_KEY_ID`: Your AWS access key
- `AWS_SECRET_ACCESS_KEY`: Your AWS secret key

### 4. Customize Variables

Edit `variables.tf` to customize:
- AWS region
- VPC CIDR blocks
- Availability zones
- S3 bucket name (must be globally unique)

## Deployment

The example workflow in `.github/workflows/example-aws.yml` will:

1. **On Pull Request**: Run `terraform plan` and post results as a comment
2. **On Push to Main**: Run `terraform apply` to deploy changes

## Manual Testing

You can also run Terraform commands locally:

```bash
# Export AWS credentials
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"

# Initialize
terraform init \
  -backend-config="bucket=my-terraform-state-bucket" \
  -backend-config="key=aws-example.tfstate" \
  -backend-config="region=us-east-1"

# Plan
terraform plan

# Apply
terraform apply

# Destroy
terraform destroy
```

## Module References

This example uses CloudOps embedded modules:

- `../../modules/aws/vpc`
- `../../modules/aws/s3-bucket`

You can customize these modules by modifying the module configuration in `main.tf`.

## Cost Considerations

This example creates resources that may incur costs:

- **NAT Gateway**: ~$0.045/hour + data processing charges
- **S3 Storage**: Based on storage amount
- **Data Transfer**: Egress from NAT Gateway

To minimize costs:
- Set `enable_nat_gateway = false` if you don't need private subnet internet access
- Delete resources when not in use

## Clean Up

To remove all resources:

```bash
terraform destroy
```

**Note**: Ensure all S3 buckets are empty before destroying, or enable `force_destroy` on the bucket resource.
