output "main_db_endpoint" {
  description = "Endpoint de la base de datos principal"
  value       = aws_db_instance.main.endpoint
}

output "main_db_name" {
  description = "Nombre de la base de datos principal"
  value       = aws_db_instance.main.db_name
}

output "persistence_db_endpoint" {
  description = "Endpoint de la base de datos de persistencia"
  value       = aws_db_instance.persistence.endpoint
}

output "persistence_db_name" {
  description = "Nombre de la base de datos de persistencia"
  value       = aws_db_instance.persistence.db_name
}

output "auth0_db_endpoint" {
  description = "Endpoint de la base de datos Auth0"
  value       = aws_db_instance.auth0.endpoint
}

output "auth0_db_name" {
  description = "Nombre de la base de datos Auth0"
  value       = aws_db_instance.auth0.db_name
}

