variable "project_name" {
  description = "Nombre del proyecto"
  type        = string
}

variable "environment" {
  description = "Ambiente de despliegue"
  type        = string
}

variable "create_order_function_arn" {
  description = "ARN de la función Lambda crear pedido"
  type        = string
}

variable "create_order_function_name" {
  description = "Nombre de la función Lambda crear pedido"
  type        = string
}

variable "check_consistency_function_arn" {
  description = "ARN de la función Lambda verificar consistencia"
  type        = string
}

variable "check_consistency_function_name" {
  description = "Nombre de la función Lambda verificar consistencia"
  type        = string
}

