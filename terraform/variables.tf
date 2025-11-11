variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "vpc_cidr" { type = string default = "10.0.0.0/16" }
variable "public_subnet_cidr" { type = string default = "10.0.1.0/24" }
variable "private_subnet_cidr" { type = string default = "10.0.2.0/24" }

variable "ssh_key_name" { type = string }
variable "ssh_public_key_path" { type = string }

variable "ssh_allowed_cidr" { type = string default = "0.0.0.0/0" }

variable "ec2_instance_type" { type = string default = "t3.micro" }
variable "rds_instance_class" { type = string default = "db.t3.micro" }

variable "db_name"     { type = string default = "wmsdb" }
variable "db_username" { type = string default = "wmsadmin" }
variable "db_password" { type = string } # sensitive - provide at runtime
