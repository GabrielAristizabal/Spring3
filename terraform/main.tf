terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  required_version = ">= 1.3.0"
}

provider "aws" {
  region = var.aws_region
}

# VPC
resource "aws_vpc" "main" {
  cidr_block = var.vpc_cidr
  tags = { Name = "wms-vpc" }
}

# Subnets
resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidr
  map_public_ip_on_launch = true
  availability_zone       = data.aws_availability_zones.available.names[0]
  tags = { Name = "wms-public-subnet" }
}

resource "aws_subnet" "private" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnet_cidr
  availability_zone = data.aws_availability_zones.available.names[0]
  tags = { Name = "wms-private-subnet" }
}

data "aws_availability_zones" "available" {}

# Internet gateway + route for public subnet
resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id
  tags = { Name = "wms-igw" }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }
  tags = { Name = "wms-public-rt" }
}

resource "aws_route_table_association" "pub_assoc" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# Security groups
resource "aws_security_group" "ec2_sg" {
  name        = "wms-ec2-sg"
  description = "Allow SSH/HTTP from allowed CIDR"
  vpc_id      = aws_vpc.main.id

  ingress {
    description      = "SSH"
    from_port        = 22
    to_port          = 22
    protocol         = "tcp"
    cidr_blocks      = [var.ssh_allowed_cidr]
  }
  ingress {
    description = "HTTP (Flask)"
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = [var.ssh_allowed_cidr]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = { Name = "wms-ec2-sg" }
}

resource "aws_security_group" "rds_sg" {
  name        = "wms-rds-sg"
  description = "Allow Postgres from EC2"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ec2_sg.id]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = { Name = "wms-rds-sg" }
}

# Key pair (use an existing key name)
resource "aws_key_pair" "deployer" {
  key_name   = var.ssh_key_name
  public_key = file(var.ssh_public_key_path)
}

# IAM role for EC2 to allow CloudWatch & KMS decrypt (minimal)
resource "aws_iam_role" "ec2_role" {
  name = "wms-ec2-role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume.json
}

data "aws_iam_policy_document" "ec2_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy_attachment" "cw_attach" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
}

resource "aws_iam_role_policy" "kms_policy" {
  name = "wms-ec2-kms"
  role = aws_iam_role.ec2_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:Sign",
          "kms:Verify",
          "kms:GetPublicKey"
        ]
        Resource = aws_kms_key.wms.arn
      }
    ]
  })
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "wms-ec2-profile"
  role = aws_iam_role.ec2_role.name
}

# KMS key for signing (customer-managed)
resource "aws_kms_key" "wms" {
  description             = "KMS key for signing operation hashes"
  deletion_window_in_days = 7
  tags = { Name = "wms-kms" }
}

resource "aws_kms_alias" "wms_alias" {
  name          = "alias/wms-signing"
  target_key_id = aws_kms_key.wms.key_id
}

# EC2 instance (Flask app)
resource "aws_instance" "app" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.ec2_instance_type
  subnet_id                   = aws_subnet.public.id
  vpc_security_group_ids      = [aws_security_group.ec2_sg.id]
  key_name                    = aws_key_pair.deployer.key_name
  iam_instance_profile        = aws_iam_instance_profile.ec2_profile.name
  user_data                   = file("${path.module}/user_data.sh")
  tags = { Name = "wms-flask-app" }
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*"]
  }
}

# RDS PostgreSQL in private subnet
resource "aws_db_subnet_group" "rds_subnet" {
  name       = "wms-rds-subnet"
  subnet_ids = [aws_subnet.private.id]
  tags = { Name = "wms-rds-subnet" }
}

resource "aws_db_instance" "postgres" {
  identifier              = "wms-postgres"
  engine                  = "postgres"
  engine_version          = "14"
  instance_class          = var.rds_instance_class
  allocated_storage       = 20
  name                    = var.db_name
  username                = var.db_username
  password                = var.db_password
  db_subnet_group_name    = aws_db_subnet_group.rds_subnet.name
  vpc_security_group_ids  = [aws_security_group.rds_sg.id]
  skip_final_snapshot     = true
  publicly_accessible     = false
  deletion_protection     = false
  tags = { Name = "wms-postgres" }
}

# CloudWatch log group for application logs
resource "aws_cloudwatch_log_group" "app_logs" {
  name              = "/wms/app"
  retention_in_days = 14
}

# Outputs
output "ec2_public_ip" {
  value = aws_instance.app.public_ip
}

output "rds_endpoint" {
  value = aws_db_instance.postgres.address
}

output "kms_key_arn" {
  value = aws_kms_key.wms.arn
}
