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

variable "subnet_ids" {
  description = "IDs de las subnets"
  type        = list(string)
}

variable "security_group_ids" {
  description = "IDs de los security groups"
  type        = list(string)
}

variable "db_endpoint" {
  description = "Endpoint de la base de datos principal"
  type        = string
}

variable "db_name" {
  description = "Nombre de la base de datos principal"
  type        = string
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

variable "persistence_db_endpoint" {
  description = "Endpoint de la base de datos de persistencia"
  type        = string
}

variable "persistence_db_name" {
  description = "Nombre de la base de datos de persistencia"
  type        = string
}

variable "validation_function_arn" {
  description = "ARN de la función Lambda validador"
  type        = string
}

variable "anomaly_function_arn" {
  description = "ARN de la función Lambda gestor de anomalías"
  type        = string
}

variable "cloudwatch_log_group" {
  description = "Nombre del grupo de logs de CloudWatch"
  type        = string
}

variable "django_image" {
  description = "Imagen Docker para Django"
  type        = string
  default     = "django:latest"
}

variable "django_cpu" {
  description = "CPU para contenedores Django"
  type        = number
  default     = 256
}

variable "django_memory" {
  description = "Memoria para contenedores Django"
  type        = number
  default     = 512
}

