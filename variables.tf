variable "aws_region" {
  description = "AWS region donde se desplegará la infraestructura"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Nombre del proyecto"
  type        = string
  default     = "spring3-order-system"
}

variable "environment" {
  description = "Ambiente de despliegue (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "vpc_cidr" {
  description = "CIDR block para la VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Zonas de disponibilidad a usar"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "db_instance_class" {
  description = "Clase de instancia RDS"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "Almacenamiento asignado a la base de datos (GB)"
  type        = number
  default     = 20
}

variable "db_username" {
  description = "Usuario de la base de datos"
  type        = string
  default     = "admin"
  sensitive   = true
}

variable "db_password" {
  description = "Contraseña de la base de datos"
  type        = string
  sensitive   = true
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

variable "enable_deletion_protection" {
  description = "Habilitar protección contra eliminación de RDS"
  type        = bool
  default     = false
}

