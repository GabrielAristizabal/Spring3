variable "project_name" {
  description = "Nombre del proyecto"
  type        = string
}

variable "environment" {
  description = "Ambiente de despliegue"
  type        = string
}

variable "validator_function_name" {
  description = "Nombre de la función Lambda validador"
  type        = string
}

variable "anomaly_function_name" {
  description = "Nombre de la función Lambda gestor de anomalías"
  type        = string
}

variable "sync_function_name" {
  description = "Nombre de la función Lambda sincronizador"
  type        = string
}

variable "audit_function_name" {
  description = "Nombre de la función Lambda auditoría"
  type        = string
}

