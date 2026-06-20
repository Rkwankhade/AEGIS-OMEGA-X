# AEGIS OMEGA X — MEGA LAYER 1
# PLANETARY DIGITAL TWIN — TERRAFORM INFRASTRUCTURE
# Multi-cloud, multi-region deployment

terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.24"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.12"
    }
  }

  backend "s3" {
    bucket         = "aegis-omega-x-tfstate"
    key            = "pdt/terraform.tfstate"
    region         = "ap-south-1"
    encrypt        = true
    dynamodb_table = "aegis-tf-locks"
  }
}

# ──────────────────────────────────────────────
# VARIABLES
# ──────────────────────────────────────────────

variable "primary_region" {
  default = "ap-south-1"
}

variable "secondary_region" {
  default = "us-east-1"
}

variable "tertiary_region" {
  default = "eu-west-1"
}

variable "cluster_name" {
  default = "aegis-omega-x-pdt"
}

variable "node_instance_type" {
  default = "m6i.4xlarge"
}

variable "neo4j_instance_type" {
  default = "r6i.8xlarge"
}

variable "environment" {
  default = "production"
}

# ──────────────────────────────────────────────
# PROVIDERS
# ──────────────────────────────────────────────

provider "aws" {
  region = var.primary_region
  alias  = "primary"
}

provider "aws" {
  region = var.secondary_region
  alias  = "secondary"
}

provider "aws" {
  region = var.tertiary_region
  alias  = "tertiary"
}

# ──────────────────────────────────────────────
# VPC — PRIMARY REGION
# ──────────────────────────────────────────────

module "vpc_primary" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  providers = { aws = aws.primary }

  name = "${var.cluster_name}-vpc-primary"
  cidr = "10.0.0.0/16"

  azs             = ["ap-south-1a", "ap-south-1b", "ap-south-1c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway   = true
  single_nat_gateway   = false
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    System      = "aegis-omega-x"
    Layer       = "pdt"
    Environment = var.environment
  }
}

# ──────────────────────────────────────────────
# EKS CLUSTER — PRIMARY
# ──────────────────────────────────────────────

module "eks_primary" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  providers = { aws = aws.primary }

  cluster_name    = "${var.cluster_name}-primary"
  cluster_version = "1.28"

  cluster_endpoint_public_access       = false
  cluster_endpoint_private_access      = true
  cluster_endpoint_public_access_cidrs = []

  vpc_id     = module.vpc_primary.vpc_id
  subnet_ids = module.vpc_primary.private_subnets

  eks_managed_node_groups = {
    # General workload nodes
    general = {
      min_size       = 3
      max_size       = 20
      desired_size   = 6
      instance_types = [var.node_instance_type]
      capacity_type  = "ON_DEMAND"
      disk_size      = 200

      labels = {
        role = "general"
      }

      tags = {
        System = "aegis-omega-x"
      }
    }

    # High-memory nodes for Neo4j + simulation
    memory_optimized = {
      min_size       = 3
      max_size       = 6
      desired_size   = 3
      instance_types = [var.neo4j_instance_type]
      capacity_type  = "ON_DEMAND"
      disk_size      = 500

      labels = {
        role = "memory-optimized"
      }

      taints = [{
        key    = "workload"
        value  = "neo4j"
        effect = "NO_SCHEDULE"
      }]
    }

    # Compute-optimized nodes for Rust sim core
    compute_optimized = {
      min_size       = 2
      max_size       = 10
      desired_size   = 2
      instance_types = ["c6i.8xlarge"]
      capacity_type  = "ON_DEMAND"
      disk_size      = 200

      labels = {
        role = "compute-optimized"
      }

      taints = [{
        key    = "workload"
        value  = "simulation"
        effect = "NO_SCHEDULE"
      }]
    }
  }

  cluster_addons = {
    aws-ebs-csi-driver = {
      most_recent = true
    }
    coredns = {
      most_recent = true
    }
    kube-proxy = {
      most_recent = true
    }
    vpc-cni = {
      most_recent = true
    }
  }

  tags = {
    System      = "aegis-omega-x"
    Layer       = "pdt"
    Environment = var.environment
  }
}

# ──────────────────────────────────────────────
# S3 BUCKETS (PDT Data Lake)
# ──────────────────────────────────────────────

resource "aws_s3_bucket" "pdt_data_lake" {
  provider = aws.primary
  bucket   = "aegis-omega-x-pdt-data-lake-${var.environment}"

  tags = {
    System = "aegis-omega-x"
    Layer  = "pdt"
  }
}

resource "aws_s3_bucket_versioning" "pdt_data_lake" {
  provider = aws.primary
  bucket   = aws_s3_bucket.pdt_data_lake.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "pdt_data_lake" {
  provider = aws.primary
  bucket   = aws_s3_bucket.pdt_data_lake.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "pdt_data_lake" {
  provider = aws.primary
  bucket   = aws_s3_bucket.pdt_data_lake.id

  rule {
    id     = "tier-to-glacier"
    status = "Enabled"

    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 365
      storage_class = "GLACIER"
    }
  }
}

# ──────────────────────────────────────────────
# KMS KEY (Encryption)
# ──────────────────────────────────────────────

resource "aws_kms_key" "aegis_master" {
  provider                = aws.primary
  description             = "AEGIS OMEGA X Master Encryption Key"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = {
    System = "aegis-omega-x"
  }
}

resource "aws_kms_alias" "aegis_master" {
  provider      = aws.primary
  name          = "alias/aegis-omega-x-master"
  target_key_id = aws_kms_key.aegis_master.key_id
}

# ──────────────────────────────────────────────
# OPENSEARCH CLUSTER (Security Events)
# ──────────────────────────────────────────────

resource "aws_opensearch_domain" "pdt_events" {
  provider    = aws.primary
  domain_name = "aegis-pdt-events"

  engine_version = "OpenSearch_2.9"

  cluster_config {
    instance_type          = "r6g.4xlarge.search"
    instance_count         = 3
    dedicated_master_enabled = true
    dedicated_master_type  = "m6g.large.search"
    dedicated_master_count = 3
    zone_awareness_enabled = true

    zone_awareness_config {
      availability_zone_count = 3
    }
  }

  ebs_options {
    ebs_enabled = true
    volume_type = "gp3"
    volume_size = 500
    throughput  = 500
    iops        = 3000
  }

  encrypt_at_rest {
    enabled    = true
    kms_key_id = aws_kms_key.aegis_master.key_id
  }

  node_to_node_encryption {
    enabled = true
  }

  domain_endpoint_options {
    enforce_https       = true
    tls_security_policy = "Policy-Min-TLS-1-2-2019-07"
  }

  advanced_security_options {
    enabled                        = true
    internal_user_database_enabled = false
  }

  tags = {
    System = "aegis-omega-x"
    Layer  = "pdt"
  }
}

# ──────────────────────────────────────────────
# ELASTICACHE REDIS (Simulation State Cache)
# ──────────────────────────────────────────────

resource "aws_elasticache_replication_group" "pdt_cache" {
  provider                   = aws.primary
  replication_group_id       = "aegis-pdt-cache"
  description                = "PDT Simulation State Cache"
  node_type                  = "cache.r7g.4xlarge"
  num_cache_clusters         = 3
  automatic_failover_enabled = true
  multi_az_enabled           = true
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  engine_version             = "7.1"

  subnet_group_name = aws_elasticache_subnet_group.pdt.name

  tags = {
    System = "aegis-omega-x"
  }
}

resource "aws_elasticache_subnet_group" "pdt" {
  provider   = aws.primary
  name       = "aegis-pdt-cache-subnet"
  subnet_ids = module.vpc_primary.private_subnets
}

# ──────────────────────────────────────────────
# OUTPUTS
# ──────────────────────────────────────────────

output "eks_cluster_endpoint" {
  value     = module.eks_primary.cluster_endpoint
  sensitive = true
}

output "data_lake_bucket" {
  value = aws_s3_bucket.pdt_data_lake.id
}

output "opensearch_endpoint" {
  value = aws_opensearch_domain.pdt_events.endpoint
}

output "redis_endpoint" {
  value     = aws_elasticache_replication_group.pdt_cache.primary_endpoint_address
  sensitive = true
}
