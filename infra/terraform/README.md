# X-sevenAI Infrastructure as Code

This directory contains Terraform configurations for provisioning and managing the X-sevenAI infrastructure on AWS.

## Structure

```
terraform/
├── modules/                      # Reusable Terraform modules
│   ├── vpc/                      # VPC module
│   ├── eks/                      # EKS module
│   ├── rds/                      # RDS module
│   └── redis/                    # Redis module
├── environments/                 # Environment-specific configurations
│   ├── dev/                      # Development environment
│   ├── staging/                  # Staging environment
│   └── prod/                     # Production environment
└── README.md                     # This file
```

## Prerequisites

- Terraform v1.5.0 or later
- AWS CLI configured with appropriate credentials
- S3 bucket for Terraform state (one per environment)
- DynamoDB table for state locking (one per environment)

## Getting Started

### Setting up the S3 Backend

Before applying the Terraform configurations, you need to create an S3 bucket and DynamoDB table for the Terraform state:

```bash
# Create S3 bucket for Terraform state
aws s3api create-bucket \
  --bucket x7ai-terraform-state-dev \
  --region us-west-1 \
  --create-bucket-configuration LocationConstraint=us-west-1

# Enable versioning on the S3 bucket
aws s3api put-bucket-versioning \
  --bucket x7ai-terraform-state-dev \
  --versioning-configuration Status=Enabled

# Create DynamoDB table for state locking
aws dynamodb create-table \
  --table-name x7ai-terraform-locks-dev \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-west-1
```

### Deploying the Infrastructure

1. Navigate to the environment directory:

```bash
cd environments/dev
```

2. Copy the example variables file and update it with your values:

```bash
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your preferred text editor
```

3. Initialize Terraform:

```bash
terraform init
```

4. Plan the deployment:

```bash
terraform plan -out=tfplan
```

5. Apply the changes:

```bash
terraform apply tfplan
```

## Modules

### VPC Module

Creates a VPC with public and private subnets across multiple availability zones, along with internet gateways, NAT gateways, and route tables.

### EKS Module

Provisions an Amazon EKS cluster with worker nodes for running Kubernetes workloads.

### RDS Module

Sets up an Amazon RDS PostgreSQL instance for the database backend.

### Redis Module

Creates an Amazon ElastiCache Redis cluster for caching and session management.

## Environment-Specific Configurations

Each environment (dev, staging, prod) has its own configuration with appropriate settings for that environment. The main differences are:

- **Development**: Smaller instance sizes, fewer resources, and less redundancy.
- **Staging**: Similar to production but with slightly reduced resources.
- **Production**: Larger instances, more resources, and full redundancy (Multi-AZ, etc.).

## Best Practices

- Always use `terraform plan` before applying changes.
- Use separate AWS accounts for different environments.
- Store sensitive values in AWS Secrets Manager or HashiCorp Vault, not in terraform.tfvars.
- Use remote state with locking to prevent concurrent modifications.
- Tag all resources appropriately for cost tracking and management.

## Maintenance

- Regularly update Terraform and provider versions.
- Monitor resource usage and adjust sizes as needed.
- Implement automated testing for infrastructure changes.
- Keep documentation up to date with any changes to the infrastructure.
