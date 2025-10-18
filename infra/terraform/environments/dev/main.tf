provider "aws" {
  region = var.region
}

terraform {
  backend "s3" {
    bucket         = "x7ai-terraform-state-dev"
    key            = "terraform.tfstate"
    region         = "us-west-1"
    encrypt        = true
    dynamodb_table = "x7ai-terraform-locks-dev"
  }
}

# VPC Module
module "vpc" {
  source = "../../modules/vpc"

  region               = var.region
  environment          = var.environment
  vpc_cidr            = var.vpc_cidr
  public_subnets_cidr  = var.public_subnets_cidr
  private_subnets_cidr = var.private_subnets_cidr
  availability_zones   = var.availability_zones
}

# EKS Module
module "eks" {
  source = "../../modules/eks"

  region            = var.region
  environment       = var.environment
  cluster_name      = "${var.environment}-x7ai-cluster"
  kubernetes_version = var.kubernetes_version
  vpc_id            = module.vpc.vpc_id
  subnet_ids        = module.vpc.private_subnets
  instance_types    = var.eks_instance_types
  disk_size         = var.eks_disk_size
  desired_size      = var.eks_desired_size
  min_size          = var.eks_min_size
  max_size          = var.eks_max_size
}

# RDS Module
module "rds" {
  source = "../../modules/rds"

  region                 = var.region
  environment            = var.environment
  vpc_id                 = module.vpc.vpc_id
  subnet_ids             = module.vpc.private_subnets
  allowed_security_groups = [module.eks.security_group_id]
  instance_class         = var.rds_instance_class
  allocated_storage      = var.rds_allocated_storage
  max_allocated_storage  = var.rds_max_allocated_storage
  db_name                = var.rds_db_name
  db_username            = var.rds_username
  db_password            = var.rds_password
  multi_az               = var.rds_multi_az
  skip_final_snapshot    = true
  deletion_protection    = false
  backup_retention_period = var.rds_backup_retention_period
}

# Redis Module
module "redis" {
  source = "../../modules/redis"

  region                    = var.region
  environment               = var.environment
  vpc_id                    = module.vpc.vpc_id
  subnet_ids                = module.vpc.private_subnets
  allowed_security_groups   = [module.eks.security_group_id]
  node_type                 = var.redis_node_type
  num_cache_clusters        = var.redis_num_cache_clusters
  automatic_failover_enabled = var.redis_automatic_failover_enabled
  multi_az_enabled          = var.redis_multi_az_enabled
}
