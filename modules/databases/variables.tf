variable "project_name" {
  description = "Nombre del proyecto"
  type        = string
}

variable "environment" {
  description = "Ambiente de despliegue"
  type        = string
}

variable "vpc_id" {
  description = "ID de la VPC"
  type        = string
}

variable "private_subnet_ids" {
  description = "IDs de las subnets privadas"
  type        = list(string)
}

variable "db_subnet_group" {
  description = "Nombre del DB subnet group"
  type        = string
}

variable "db_instance_class" {
  description = "Clase de instancia RDS"
  type        = string
}

variable "db_allocated_storage" {
  description = "Almacenamiento asignado (GB)"
  type        = number
}

variable "db_username" {
  description = "Usuario de la base de datos"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "Contraseña de la base de datos"
  type        = string
  sensitive   = true
}

variable "enable_deletion_protection" {
  description = "Habilitar protección contra eliminación"
  type        = bool
  default     = false
}

variable "rds_security_group_id" {
  description = "ID del security group para RDS"
  type        = string
}

