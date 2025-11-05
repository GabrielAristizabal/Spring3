terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Datos de la cuenta AWS
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Módulo de Networking
module "networking" {
  source = "./modules/networking"
  
  project_name = var.project_name
  environment  = var.environment
  vpc_cidr     = var.vpc_cidr
  availability_zones = var.availability_zones
}

# Módulo de Bases de Datos
module "databases" {
  source = "./modules/databases"
  
  project_name = var.project_name
  environment  = var.environment
  
  vpc_id             = module.networking.vpc_id
  private_subnet_ids = module.networking.private_subnet_ids
  db_subnet_group    = module.networking.db_subnet_group_name
  rds_security_group_id = module.networking.rds_security_group_id
  
  db_instance_class = var.db_instance_class
  db_allocated_storage = var.db_allocated_storage
  db_username = var.db_username
  db_password = var.db_password
  enable_deletion_protection = var.enable_deletion_protection
}

# Módulos comentados: Requieren permisos IAM que no están disponibles
# Para simplificar, usaremos scripts Python directos conectándose a RDS

# Módulo de SNS/SQS para comunicación asíncrona
# COMENTADO: No necesario para versión simplificada
# module "messaging" {
#   source = "./modules/messaging"
#   ...
# }

# Módulo de Lambda Functions
# COMENTADO: Requiere permisos IAM
# module "lambda_functions" {
#   ...
# }

# Módulo de ECS para Django Applications
# COMENTADO: Requiere permisos IAM
# module "django_apps" {
#   ...
# }

# Módulo de CloudWatch y Monitoreo
# COMENTADO: No necesario para versión simplificada
# module "monitoring" {
#   ...
# }

# API Gateway para exponer endpoints
# COMENTADO: Usaremos scripts Python directos en lugar de API Gateway
# module "api_gateway" {
#   ...
# }

