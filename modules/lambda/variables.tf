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

variable "validation_topic_arn" {
  description = "ARN del topic SNS de validación"
  type        = string
}

variable "anomaly_topic_arn" {
  description = "ARN del topic SNS de anomalías"
  type        = string
}

variable "audit_topic_arn" {
  description = "ARN del topic SNS de auditoría"
  type        = string
}

variable "order_queue_url" {
  description = "URL de la queue SQS de pedidos"
  type        = string
}

variable "order_queue_arn" {
  description = "ARN de la queue SQS de pedidos"
  type        = string
}

variable "validation_queue_url" {
  description = "URL de la queue SQS de validación"
  type        = string
}

variable "validation_queue_arn" {
  description = "ARN de la queue SQS de validación"
  type        = string
}

variable "anomaly_queue_url" {
  description = "URL de la queue SQS de anomalías"
  type        = string
}

variable "anomaly_queue_arn" {
  description = "ARN de la queue SQS de anomalías"
  type        = string
}

variable "persistence_db_endpoint" {
  description = "Endpoint de la base de datos de persistencia"
  type        = string
}

variable "persistence_db_name" {
  description = "Nombre de la base de datos de persistencia"
  type        = string
}

variable "validation_dlq_arn" {
  description = "ARN de la Dead Letter Queue de validación"
  type        = string
}

variable "anomaly_dlq_arn" {
  description = "ARN de la Dead Letter Queue de anomalías"
  type        = string
}

variable "lambda_role_arn" {
  description = "ARN del rol IAM existente para Lambda (opcional, si no se proporciona se intentará crear uno)"
  type        = string
  default     = null
}

