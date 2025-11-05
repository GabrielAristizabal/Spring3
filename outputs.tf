output "vpc_id" {
  description = "ID de la VPC creada"
  value       = module.networking.vpc_id
}

output "api_gateway_url" {
  description = "URL del API Gateway"
  value       = module.api_gateway.api_gateway_url
}

output "main_db_endpoint" {
  description = "Endpoint de la base de datos principal"
  value       = module.databases.main_db_endpoint
  sensitive   = true
}

output "persistence_db_endpoint" {
  description = "Endpoint de la base de datos de persistencia"
  value       = module.databases.persistence_db_endpoint
  sensitive   = true
}

output "validator_function_arn" {
  description = "ARN de la función Lambda validador"
  value       = module.lambda_functions.validator_function_arn
}

output "anomaly_function_arn" {
  description = "ARN de la función Lambda gestor de anomalías"
  value       = module.lambda_functions.anomaly_function_arn
}

output "cloudwatch_dashboard_url" {
  description = "URL del dashboard de CloudWatch"
  value       = module.monitoring.dashboard_url
}

output "consistency_log_group_name" {
  description = "Nombre del grupo de logs de consistencia"
  value       = module.monitoring.consistency_log_group_name
}

