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

# Módulo de SNS/SQS para comunicación asíncrona
module "messaging" {
  source = "./modules/messaging"
  
  project_name = var.project_name
  environment  = var.environment
}

# Módulo de Lambda Functions
module "lambda_functions" {
  source = "./modules/lambda"
  
  project_name = var.project_name
  environment  = var.environment
  
  vpc_id             = module.networking.vpc_id
  subnet_ids         = module.networking.private_subnet_ids
  security_group_ids = [module.networking.lambda_security_group_id]
  
  db_endpoint         = module.databases.main_db_endpoint
  db_name            = module.databases.main_db_name
  db_username        = var.db_username
  db_password        = var.db_password
  
  persistence_db_endpoint = module.databases.persistence_db_endpoint
  persistence_db_name     = module.databases.persistence_db_name
  
  # Topics SNS
  validation_topic_arn    = module.messaging.validation_topic_arn
  anomaly_topic_arn       = module.messaging.anomaly_topic_arn
  audit_topic_arn         = module.messaging.audit_topic_arn
  
  # Queues SQS
  order_queue_url         = module.messaging.order_queue_url
  order_queue_arn         = module.messaging.order_queue_arn
  validation_queue_url    = module.messaging.validation_queue_url
  validation_queue_arn    = module.messaging.validation_queue_arn
  anomaly_queue_url       = module.messaging.anomaly_queue_url
  anomaly_queue_arn       = module.messaging.anomaly_queue_arn
  
  # Dead Letter Queues
  validation_dlq_arn     = module.messaging.validation_dlq_arn
  anomaly_dlq_arn         = module.messaging.anomaly_dlq_arn
}

# Módulo de ECS para Django Applications
module "django_apps" {
  source = "./modules/django"
  
  project_name = var.project_name
  environment  = var.environment
  
  vpc_id             = module.networking.vpc_id
  subnet_ids         = module.networking.private_subnet_ids
  security_group_ids = [module.networking.django_security_group_id]
  
  db_endpoint         = module.databases.main_db_endpoint
  db_name            = module.databases.main_db_name
  db_username        = var.db_username
  db_password        = var.db_password
  
  persistence_db_endpoint = module.databases.persistence_db_endpoint
  persistence_db_name     = module.databases.persistence_db_name
  
  validation_function_arn = module.lambda_functions.validator_function_arn
  anomaly_function_arn    = module.lambda_functions.anomaly_function_arn
  
  cloudwatch_log_group = module.monitoring.consistency_log_group_name
}

# Módulo de CloudWatch y Monitoreo
module "monitoring" {
  source = "./modules/monitoring"
  
  project_name = var.project_name
  environment  = var.environment
  
  validator_function_name = module.lambda_functions.validator_function_name
  anomaly_function_name   = module.lambda_functions.anomaly_function_name
  sync_function_name      = module.lambda_functions.sync_function_name
  audit_function_name     = module.lambda_functions.audit_function_name
}

# API Gateway para exponer endpoints
module "api_gateway" {
  source = "./modules/api_gateway"
  
  project_name = var.project_name
  environment  = var.environment
  
  create_order_function_arn = module.lambda_functions.create_order_function_arn
  create_order_function_name = module.lambda_functions.create_order_function_name
  check_consistency_function_arn = module.lambda_functions.check_consistency_function_arn
  check_consistency_function_name = module.lambda_functions.check_consistency_function_name
}

