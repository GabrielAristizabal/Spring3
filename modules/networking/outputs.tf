output "vpc_id" {
  description = "ID de la VPC"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "IDs de las subnets públicas"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "IDs de las subnets privadas"
  value       = aws_subnet.private[*].id
}

output "db_subnet_ids" {
  description = "IDs de las subnets de base de datos"
  value       = aws_subnet.db[*].id
}

output "db_subnet_group_name" {
  description = "Nombre del DB subnet group"
  value       = aws_db_subnet_group.main.name
}

output "lambda_security_group_id" {
  description = "ID del security group para Lambda"
  value       = aws_security_group.lambda.id
}

output "django_security_group_id" {
  description = "ID del security group para Django"
  value       = aws_security_group.django.id
}

output "rds_security_group_id" {
  description = "ID del security group para RDS"
  value       = aws_security_group.rds.id
}

