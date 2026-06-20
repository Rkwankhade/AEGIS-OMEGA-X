# AEGIS OMEGA X — TERRAFORM MODULES
# DEPLOY/terraform/modules/eks/main.tf
# Production-grade EKS cluster module

terraform {
  required_providers {
    aws        = { source = "hashicorp/aws",        version = "~> 5.0" }
    kubernetes = { source = "hashicorp/kubernetes",  version = "~> 2.24" }
    helm       = { source = "hashicorp/helm",        version = "~> 2.12" }
    tls        = { source = "hashicorp/tls",         version = "~> 4.0" }
  }
}

# ──────────────────────────────────────────────
# VARIABLES
# ──────────────────────────────────────────────
variable "cluster_name"        { type = string }
variable "cluster_version"     { type = string  default = "1.29" }
variable "vpc_id"              { type = string }
variable "private_subnet_ids"  { type = list(string) }
variable "environment"         { type = string  default = "production" }
variable "kms_key_arn"         { type = string  default = "" }

variable "node_groups" {
  type = map(object({
    instance_types = list(string)
    min_size       = number
    max_size       = number
    desired_size   = number
    disk_size      = number
    capacity_type  = string
    labels         = map(string)
    taints         = list(object({ key = string, value = string, effect = string }))
  }))
  default = {}
}

# ──────────────────────────────────────────────
# IAM ROLES
# ──────────────────────────────────────────────
data "aws_iam_policy_document" "eks_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["eks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "eks_cluster" {
  name               = "${var.cluster_name}-cluster-role"
  assume_role_policy = data.aws_iam_policy_document.eks_assume_role.json
  tags               = { System = "aegis-omega-x", Environment = var.environment }
}

resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.eks_cluster.name
}

resource "aws_iam_role_policy_attachment" "eks_vpc_resource_controller" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSVPCResourceController"
  role       = aws_iam_role.eks_cluster.name
}

data "aws_iam_policy_document" "node_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "eks_node" {
  name               = "${var.cluster_name}-node-role"
  assume_role_policy = data.aws_iam_policy_document.node_assume_role.json
  tags               = { System = "aegis-omega-x" }
}

resource "aws_iam_role_policy_attachment" "eks_worker_node" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.eks_node.name
}

resource "aws_iam_role_policy_attachment" "eks_cni" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.eks_node.name
}

resource "aws_iam_role_policy_attachment" "ecr_readonly" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.eks_node.name
}

resource "aws_iam_role_policy_attachment" "ssm_managed" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
  role       = aws_iam_role.eks_node.name
}

# ──────────────────────────────────────────────
# SECURITY GROUPS
# ──────────────────────────────────────────────
resource "aws_security_group" "eks_cluster" {
  name        = "${var.cluster_name}-cluster-sg"
  description = "EKS cluster security group"
  vpc_id      = var.vpc_id

  ingress {
    description = "Allow nodes to communicate with cluster API"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.cluster_name}-cluster-sg", System = "aegis-omega-x" }
}

resource "aws_security_group" "eks_nodes" {
  name        = "${var.cluster_name}-nodes-sg"
  description = "EKS nodes security group"
  vpc_id      = var.vpc_id

  ingress {
    description = "Allow inter-node communication"
    from_port   = 0
    to_port     = 65535
    protocol    = "-1"
    self        = true
  }

  ingress {
    description     = "Allow cluster API to nodes"
    from_port       = 1025
    to_port         = 65535
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_cluster.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.cluster_name}-nodes-sg", System = "aegis-omega-x" }
}

# ──────────────────────────────────────────────
# EKS CLUSTER
# ──────────────────────────────────────────────
resource "aws_eks_cluster" "main" {
  name     = var.cluster_name
  version  = var.cluster_version
  role_arn = aws_iam_role.eks_cluster.arn

  vpc_config {
    subnet_ids              = var.private_subnet_ids
    security_group_ids      = [aws_security_group.eks_cluster.id]
    endpoint_private_access = true
    endpoint_public_access  = false
  }

  encryption_config {
    provider {
      key_arn = var.kms_key_arn != "" ? var.kms_key_arn : null
    }
    resources = ["secrets"]
  }

  enabled_cluster_log_types = [
    "api", "audit", "authenticator",
    "controllerManager", "scheduler"
  ]

  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster_policy,
    aws_iam_role_policy_attachment.eks_vpc_resource_controller,
  ]

  tags = { System = "aegis-omega-x", Environment = var.environment }
}

# ──────────────────────────────────────────────
# EKS MANAGED NODE GROUPS
# ──────────────────────────────────────────────
resource "aws_eks_node_group" "groups" {
  for_each = var.node_groups

  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "${var.cluster_name}-${each.key}"
  node_role_arn   = aws_iam_role.eks_node.arn
  subnet_ids      = var.private_subnet_ids
  instance_types  = each.value.instance_types
  capacity_type   = each.value.capacity_type
  disk_size       = each.value.disk_size

  scaling_config {
    min_size     = each.value.min_size
    max_size     = each.value.max_size
    desired_size = each.value.desired_size
  }

  update_config {
    max_unavailable = 1
  }

  labels = each.value.labels

  dynamic "taint" {
    for_each = each.value.taints
    content {
      key    = taint.value.key
      value  = taint.value.value
      effect = taint.value.effect
    }
  }

  lifecycle {
    ignore_changes = [scaling_config[0].desired_size]
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_worker_node,
    aws_iam_role_policy_attachment.eks_cni,
    aws_iam_role_policy_attachment.ecr_readonly,
  ]

  tags = { System = "aegis-omega-x", Environment = var.environment }
}

# ──────────────────────────────────────────────
# EKS ADD-ONS
# ──────────────────────────────────────────────
resource "aws_eks_addon" "vpc_cni" {
  cluster_name             = aws_eks_cluster.main.name
  addon_name               = "vpc-cni"
  resolve_conflicts_on_update = "OVERWRITE"
  tags                     = { System = "aegis-omega-x" }
}

resource "aws_eks_addon" "coredns" {
  cluster_name             = aws_eks_cluster.main.name
  addon_name               = "coredns"
  resolve_conflicts_on_update = "OVERWRITE"
  depends_on               = [aws_eks_node_group.groups]
  tags                     = { System = "aegis-omega-x" }
}

resource "aws_eks_addon" "kube_proxy" {
  cluster_name             = aws_eks_cluster.main.name
  addon_name               = "kube-proxy"
  resolve_conflicts_on_update = "OVERWRITE"
  tags                     = { System = "aegis-omega-x" }
}

resource "aws_eks_addon" "ebs_csi" {
  cluster_name             = aws_eks_cluster.main.name
  addon_name               = "aws-ebs-csi-driver"
  resolve_conflicts_on_update = "OVERWRITE"
  depends_on               = [aws_eks_node_group.groups]
  tags                     = { System = "aegis-omega-x" }
}

# ──────────────────────────────────────────────
# OUTPUTS
# ──────────────────────────────────────────────
output "cluster_name"     { value = aws_eks_cluster.main.name }
output "cluster_endpoint" { value = aws_eks_cluster.main.endpoint  sensitive = true }
output "cluster_ca"       { value = aws_eks_cluster.main.certificate_authority[0].data sensitive = true }
output "cluster_version"  { value = aws_eks_cluster.main.version }
output "node_role_arn"    { value = aws_iam_role.eks_node.arn }
output "node_sg_id"       { value = aws_security_group.eks_nodes.id }
