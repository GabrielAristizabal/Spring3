######################################
# VARIABLES PRINCIPALES DE DEPLOYMENT
######################################

# Región de AWS
variable "region" {
  type    = string
  default = "us-east-1"
  description = "Región donde se desplegarán los recursos."
}

# Nombre del proyecto
variable "project_name" {
  type    = string
  default = "wms-no-repudio"
  description = "Prefijo para los recursos creados en AWS."
}

######################################
# RED Y VPC
######################################

# CIDR de la VPC principal
variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
  description = "Bloque CIDR de la VPC."
}

# CIDR de las subnets públicas (por ejemplo, EC2 y API Gateway)
variable "public_subnet_cidr" {
  type    = string
  default = "10.0.1.0/24"
  description = "Bloque CIDR de la subred pública."
}

# CIDR de las subnets privadas (por ejemplo, base de datos)
variable "private_subnet_cidr" {
  type    = string
  default = "10.0.2.0/24"
  description = "Bloque CIDR de la subred privada."
}

######################################
# CONFIGURACIÓN DE EC2 (Flask backend)
######################################

variable "instance_type" {
  type    = string
  default = "t3.micro"
  description = "Tipo de instancia EC2 para el backend Flask."
}

variable "key_pair_name" {
  type        = string
  description = "Nombre del par de claves existente para conectarse a la EC2."
}

######################################
# CONFIGURACIÓN DE BASE DE DATOS RDS
######################################

variable "db_username" {
  type    = string
  default = "admin"
  description = "Usuario administrador de la base de datos PostgreSQL."
}

variable "db_password" {
  type        = string
  description = "Contraseña del usuario administrador de la base de datos."
  sensitive   = true
}

variable "db_name" {
  type    = string
  default = "wmsdb"
  description = "Nombre de la base de datos PostgreSQL."
}

variable "db_instance_class" {
  type    = string
  default = "db.t3.micro"
  description = "Tipo de instancia para RDS PostgreSQL."
}

######################################
# CONFIGURACIÓN DE LOGS Y MONITOREO
######################################

variable "enable_cloudwatch_logs" {
  type    = bool
  default = true
  description = "Si se habilitan los logs en CloudWatch."
}

variable "enable_s3_logs" {
  type    = bool
  default = true
  description = "Si se habilita el almacenamiento de logs en S3."
}

######################################
# CONFIGURACIÓN DE AUTENTICACIÓN (Auth0)
######################################

variable "auth0_domain" {
  type        = string
  description = "Dominio de Auth0 (por ejemplo: example.us.auth0.com)."
}

variable "auth0_audience" {
  type        = string
  description = "Audiencia configurada en Auth0 para validar los tokens JWT."
}

variable "auth0_client_id" {
  type        = string
  description = "ID del cliente de Auth0 para integración con Flask."
}

######################################
# CONFIGURACIÓN ADICIONAL
######################################

variable "availability_zone" {
  type    = string
  default = "us-east-1a"
  description = "Zona de disponibilidad para las subredes."
}

variable "allowed_cidr" {
  type    = string
  default = "0.0.0.0/0"
  description = "CIDR permitido para acceso (solo usar 0.0.0.0/0 para pruebas)."
}
