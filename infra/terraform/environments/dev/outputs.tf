output "vpc_id" {
  description = "The ID of the VPC"
  value       = module.vpc.vpc_id
}

output "public_subnets" {
  description = "List of IDs of public subnets"
  value       = module.vpc.public_subnets
}

output "private_subnets" {
  description = "List of IDs of private subnets"
  value       = module.vpc.private_subnets
}

output "eks_cluster_id" {
  description = "The ID of the EKS cluster"
  value       = module.eks.cluster_id
}

output "eks_cluster_name" {
  description = "The name of the EKS cluster"
  value       = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  description = "The endpoint for the EKS cluster"
  value       = module.eks.cluster_endpoint
}

output "eks_cluster_certificate_authority_data" {
  description = "The certificate authority data for the EKS cluster"
  value       = module.eks.cluster_certificate_authority_data
}

output "rds_endpoint" {
  description = "The endpoint of the RDS instance"
  value       = module.rds.rds_endpoint
}

output "rds_address" {
  description = "The address of the RDS instance"
  value       = module.rds.rds_address
}

output "rds_port" {
  description = "The port of the RDS instance"
  value       = module.rds.rds_port
}

output "rds_name" {
  description = "The name of the RDS instance"
  value       = module.rds.rds_name
}

output "redis_endpoint" {
  description = "The endpoint of the Redis cluster"
  value       = module.redis.redis_endpoint
}

output "redis_port" {
  description = "The port of the Redis cluster"
  value       = module.redis.redis_port
}
