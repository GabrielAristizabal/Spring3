output "vpc_id" {
  description = "ID de la VPC creada"
  value       = module.networking.vpc_id
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

output "main_db_name" {
  description = "Nombre de la base de datos principal"
  value       = module.databases.main_db_name
}

output "persistence_db_name" {
  description = "Nombre de la base de datos de persistencia"
  value       = module.databases.persistence_db_name
}

