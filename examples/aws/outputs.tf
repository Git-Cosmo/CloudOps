output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "public_subnet_ids" {
  description = "IDs of public subnets"
  value       = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  description = "IDs of private subnets"
  value       = module.vpc.private_subnet_ids
}

output "data_bucket_name" {
  description = "Name of the data bucket"
  value       = module.data_bucket.bucket_id
}

output "data_bucket_arn" {
  description = "ARN of the data bucket"
  value       = module.data_bucket.bucket_arn
}
