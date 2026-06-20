# AEGIS OMEGA X — TERRAFORM PRODUCTION ENVIRONMENT
# DEPLOY/terraform/environments/production/main.tf
# Multi-region, multi-AZ production deployment

terraform {
  required_version = ">= 1.7.0"
  required_providers {
    aws        = { source = "hashicorp/aws",        version = "~> 5.0" }
    kubernetes = { source = "hashicorp/kubernetes",  version = "~> 2.24" }
    helm       = { source = "hashicorp/helm",        version = "~> 2.12" }
    random     = { source = "hashicorp/random",      version = "~> 3.6" }
  }
  backend "s3" {
    bucket         = "aegis-omega-x-tfstate-prod"
    key            = "production/terraform.tfstate"
    region         = "ap-south-1"
    encrypt        = true
    dynamodb_table = "aegis-tf-locks-prod"
    kms_key_id     = "alias/aegis-omega-x-tfstate"
  }
}

# ──────────────────────────────────────────────
# LOCALS
# ──────────────────────────────────────────────
locals {
  env         = "production"
  primary_region    = "ap-south-1"
  secondary_region  = "us-east-1"
  tertiary_region   = "eu-west-1"
  cluster_name      = "aegis-omega-x-prod"
  namespace         = "aegis-omega-x"

  common_tags = {
    System      = "aegis-omega-x"
    Environment = local.env
    ManagedBy   = "terraform"
    Owner       = "security-platform-team"
  }
}

# ──────────────────────────────────────────────
# PROVIDERS
# ──────────────────────────────────────────────
provider "aws" {
  region = local.primary_region
  alias  = "primary"
  default_tags { tags = local.common_tags }
}

provider "aws" {
  region = local.secondary_region
  alias  = "secondary"
  default_tags { tags = local.common_tags }
}

provider "aws" {
  region = local.tertiary_region
  alias  = "tertiary"
  default_tags { tags = local.common_tags }
}

# ──────────────────────────────────────────────
# KMS KEYS
# ──────────────────────────────────────────────
resource "aws_kms_key" "master" {
  provider                = aws.primary
  description             = "AEGIS OMEGA X Master Encryption Key"
  deletion_window_in_days = 30
  enable_key_rotation     = true
  multi_region            = true
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = { AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root" }
        Action   = "kms:*"
        Resource = "*"
      }
    ]
  })
}

resource "aws_kms_alias" "master" {
  provider      = aws.primary
  name          = "alias/aegis-omega-x-master"
  target_key_id = aws_kms_key.master.key_id
}

data "aws_caller_identity" "current" { provider = aws.primary }
data "aws_availability_zones" "primary" {
  provider = aws.primary
  state    = "available"
}

# ──────────────────────────────────────────────
# VPC — PRIMARY REGION (ap-south-1)
# ──────────────────────────────────────────────
module "vpc_primary" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"
  providers = { aws = aws.primary }

  name = "${local.cluster_name}-vpc-primary"
  cidr = "10.0.0.0/16"

  azs = [
    "${local.primary_region}a",
    "${local.primary_region}b",
    "${local.primary_region}c"
  ]
  private_subnets  = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets   = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
  database_subnets = ["10.0.201.0/24", "10.0.202.0/24", "10.0.203.0/24"]

  enable_nat_gateway               = true
  single_nat_gateway               = false
  one_nat_gateway_per_az           = true
  enable_dns_hostnames             = true
  enable_dns_support               = true
  enable_flow_log                  = true
  flow_log_destination_type        = "cloud-watch-logs"
  create_flow_log_cloudwatch_iam_role  = true
  create_flow_log_cloudwatch_log_group = true

  private_subnet_tags = {
    "kubernetes.io/cluster/${local.cluster_name}" = "shared"
    "kubernetes.io/role/internal-elb"             = "1"
  }
  public_subnet_tags = {
    "kubernetes.io/cluster/${local.cluster_name}" = "shared"
    "kubernetes.io/role/elb"                      = "1"
  }
}

# ──────────────────────────────────────────────
# EKS CLUSTER — PRIMARY
# ──────────────────────────────────────────────
module "eks_primary" {
  source = "../../modules/eks"
  providers = { aws = aws.primary }

  cluster_name       = local.cluster_name
  cluster_version    = "1.29"
  vpc_id             = module.vpc_primary.vpc_id
  private_subnet_ids = module.vpc_primary.private_subnets
  environment        = local.env
  kms_key_arn        = aws_kms_key.master.arn

  node_groups = {
    general = {
      instance_types = ["m6i.4xlarge"]
      min_size       = 3
      max_size       = 20
      desired_size   = 6
      disk_size      = 200
      capacity_type  = "ON_DEMAND"
      labels         = { role = "general", system = "aegis-omega-x" }
      taints         = []
    }
    memory_optimized = {
      instance_types = ["r6i.8xlarge"]
      min_size       = 3
      max_size       = 6
      desired_size   = 3
      disk_size      = 500
      capacity_type  = "ON_DEMAND"
      labels         = { role = "memory-optimized", workload = "neo4j" }
      taints         = [{ key = "workload", value = "neo4j", effect = "NO_SCHEDULE" }]
    }
    compute_optimized = {
      instance_types = ["c6i.8xlarge"]
      min_size       = 2
      max_size       = 10
      desired_size   = 2
      disk_size      = 200
      capacity_type  = "ON_DEMAND"
      labels         = { role = "compute-optimized", workload = "simulation" }
      taints         = [{ key = "workload", value = "simulation", effect = "NO_SCHEDULE" }]
    }
    spot_general = {
      instance_types = ["m6i.4xlarge", "m5.4xlarge", "m5a.4xlarge"]
      min_size       = 0
      max_size       = 30
      desired_size   = 3
      disk_size      = 200
      capacity_type  = "SPOT"
      labels         = { role = "spot-general" }
      taints         = [{ key = "spot", value = "true", effect = "PREFER_NO_SCHEDULE" }]
    }
  }
}

# ──────────────────────────────────────────────
# ECR REPOSITORIES
# ──────────────────────────────────────────────
locals {
  ecr_repos = [
    "pdt-api", "genome-api", "knowledge-api",
    "aegis-gateway", "sim-core", "pdt-frontend"
  ]
}

resource "aws_ecr_repository" "repos" {
  provider = aws.primary
  for_each = toset(local.ecr_repos)

  name                 = "aegis-omega-x/${each.key}"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "KMS"
    kms_key         = aws_kms_key.master.arn
  }
}

resource "aws_ecr_lifecycle_policy" "cleanup" {
  provider   = aws.primary
  for_each   = aws_ecr_repository.repos
  repository = each.value.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 10 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 10
      }
      action = { type = "expire" }
    }]
  })
}

# ──────────────────────────────────────────────
# RDS POSTGRESQL (Managed)
# ──────────────────────────────────────────────
resource "aws_db_subnet_group" "postgres" {
  provider   = aws.primary
  name       = "${local.cluster_name}-postgres"
  subnet_ids = module.vpc_primary.database_subnets
}

resource "random_password" "postgres" {
  length  = 32
  special = false
}

resource "aws_secretsmanager_secret" "postgres" {
  provider = aws.primary
  name     = "aegis-omega-x/postgres-credentials"
  kms_key_id = aws_kms_key.master.arn
}

resource "aws_secretsmanager_secret_version" "postgres" {
  provider  = aws.primary
  secret_id = aws_secretsmanager_secret.postgres.id
  secret_string = jsonencode({
    username = "aegis"
    password = random_password.postgres.result
    host     = aws_db_instance.postgres.address
    port     = 5432
    dbname   = "aegis_omega"
    url      = "postgresql://aegis:${random_password.postgres.result}@${aws_db_instance.postgres.address}:5432/aegis_omega"
  })
}

resource "aws_db_instance" "postgres" {
  provider               = aws.primary
  identifier             = "${local.cluster_name}-postgres"
  engine                 = "postgres"
  engine_version         = "16.1"
  instance_class         = "db.r6g.4xlarge"
  allocated_storage      = 500
  max_allocated_storage  = 5000
  storage_type           = "gp3"
  storage_encrypted      = true
  kms_key_id             = aws_kms_key.master.arn
  db_name                = "aegis_omega"
  username               = "aegis"
  password               = random_password.postgres.result
  db_subnet_group_name   = aws_db_subnet_group.postgres.name
  multi_az               = true
  publicly_accessible    = false
  deletion_protection    = true
  backup_retention_period = 30
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  auto_minor_version_upgrade = true
  performance_insights_enabled = true
  monitoring_interval    = 60
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]

  parameter_group_name = aws_db_parameter_group.postgres.name
}

resource "aws_db_parameter_group" "postgres" {
  provider = aws.primary
  name     = "${local.cluster_name}-postgres16"
  family   = "postgres16"

  parameter {
    name  = "shared_preload_libraries"
    value = "timescaledb,pg_stat_statements,pgaudit"
  }
  parameter {
    name  = "log_min_duration_statement"
    value = "1000"
  }
  parameter {
    name  = "pgaudit.log"
    value = "all"
  }
}

# ──────────────────────────────────────────────
# ELASTICACHE REDIS
# ──────────────────────────────────────────────
resource "aws_elasticache_subnet_group" "redis" {
  provider   = aws.primary
  name       = "${local.cluster_name}-redis"
  subnet_ids = module.vpc_primary.private_subnets
}

resource "aws_elasticache_replication_group" "redis" {
  provider                   = aws.primary
  replication_group_id       = "aegis-prod-cache"
  description                = "AEGIS OMEGA X Production Cache"
  node_type                  = "cache.r7g.4xlarge"
  num_cache_clusters         = 3
  automatic_failover_enabled = true
  multi_az_enabled           = true
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  kms_key_id                 = aws_kms_key.master.arn
  engine_version             = "7.2"
  subnet_group_name          = aws_elasticache_subnet_group.redis.name
  parameter_group_name       = "default.redis7"
  snapshot_retention_limit   = 7
}

# ──────────────────────────────────────────────
# S3 DATA LAKE
# ──────────────────────────────────────────────
resource "aws_s3_bucket" "data_lake" {
  provider = aws.primary
  bucket   = "aegis-omega-x-data-lake-${local.env}-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_versioning" "data_lake" {
  provider = aws.primary
  bucket   = aws_s3_bucket.data_lake.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data_lake" {
  provider = aws.primary
  bucket   = aws_s3_bucket.data_lake.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.master.arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "data_lake" {
  provider                = aws.primary
  bucket                  = aws_s3_bucket.data_lake.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "data_lake" {
  provider = aws.primary
  bucket   = aws_s3_bucket.data_lake.id

  rule {
    id     = "intelligent-tiering"
    status = "Enabled"
    transition {
      days          = 90
      storage_class = "INTELLIGENT_TIERING"
    }
    transition {
      days          = 365
      storage_class = "GLACIER_IR"
    }
    transition {
      days          = 1095
      storage_class = "DEEP_ARCHIVE"
    }
  }
}

# ──────────────────────────────────────────────
# OPENSEARCH
# ──────────────────────────────────────────────
resource "aws_opensearch_domain" "events" {
  provider    = aws.primary
  domain_name = "aegis-prod-events"
  engine_version = "OpenSearch_2.11"

  cluster_config {
    instance_type          = "r6g.4xlarge.search"
    instance_count         = 3
    dedicated_master_enabled = true
    dedicated_master_type  = "m6g.large.search"
    dedicated_master_count = 3
    zone_awareness_enabled = true
    zone_awareness_config  { availability_zone_count = 3 }
  }

  ebs_options {
    ebs_enabled = true
    volume_type = "gp3"
    volume_size = 1000
    throughput  = 1000
    iops        = 6000
  }

  encrypt_at_rest { enabled = true; kms_key_id = aws_kms_key.master.arn }
  node_to_node_encryption { enabled = true }
  domain_endpoint_options {
    enforce_https       = true
    tls_security_policy = "Policy-Min-TLS-1-2-2019-07"
  }
  advanced_security_options {
    enabled                        = true
    internal_user_database_enabled = false
  }

  auto_tune_options {
    desired_state       = "ENABLED"
    rollback_on_disable = "NO_ROLLBACK"
  }
}

# ──────────────────────────────────────────────
# CLOUDWATCH LOG GROUPS
# ──────────────────────────────────────────────
resource "aws_cloudwatch_log_group" "eks" {
  provider          = aws.primary
  name              = "/aws/eks/${local.cluster_name}/cluster"
  retention_in_days = 90
  kms_key_id        = aws_kms_key.master.arn
}

resource "aws_cloudwatch_log_group" "app_logs" {
  for_each          = toset(["pdt-api", "genome-api", "knowledge-api", "aegis-gateway"])
  provider          = aws.primary
  name              = "/aegis-omega-x/production/${each.key}"
  retention_in_days = 30
  kms_key_id        = aws_kms_key.master.arn
}

# ──────────────────────────────────────────────
# OUTPUTS
# ──────────────────────────────────────────────
output "eks_cluster_name"        { value = module.eks_primary.cluster_name }
output "eks_cluster_endpoint"    { value = module.eks_primary.cluster_endpoint    sensitive = true }
output "data_lake_bucket"        { value = aws_s3_bucket.data_lake.id }
output "redis_endpoint"          { value = aws_elasticache_replication_group.redis.primary_endpoint_address  sensitive = true }
output "postgres_secret_arn"     { value = aws_secretsmanager_secret.postgres.arn }
output "opensearch_endpoint"     { value = aws_opensearch_domain.events.endpoint }
output "ecr_registry"            { value = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${local.primary_region}.amazonaws.com" }
output "kms_key_arn"             { value = aws_kms_key.master.arn }
