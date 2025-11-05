# Base de datos principal (Gestor de pedido, Gestor bodega, Apartar unidades)
resource "aws_db_instance" "main" {
  identifier     = "${var.project_name}-${var.environment}-main-db"
  engine         = "mysql"
  engine_version = "8.0"
  instance_class = var.db_instance_class

  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_allocated_storage * 2
  storage_type         = "gp3"
  storage_encrypted     = true

  db_name  = "order_management"
  username = var.db_username
  password = var.db_password

  vpc_security_group_ids = [var.rds_security_group_id]
  db_subnet_group_name   = var.db_subnet_group

  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "mon:04:00-mon:05:00"

  skip_final_snapshot       = !var.enable_deletion_protection
  final_snapshot_identifier = var.enable_deletion_protection ? "${var.project_name}-${var.environment}-main-db-final-snapshot" : null
  deletion_protection       = var.enable_deletion_protection

  enabled_cloudwatch_logs_exports = ["error", "general", "slow_query"]

  tags = {
    Name        = "${var.project_name}-${var.environment}-main-db"
    Environment = var.environment
    Project     = var.project_name
    Component   = "order_management"
  }
}

# Base de datos de persistencia (Persistencia pedido, Persistencia bodega)
resource "aws_db_instance" "persistence" {
  identifier     = "${var.project_name}-${var.environment}-persistence-db"
  engine         = "mysql"
  engine_version = "8.0"
  instance_class = var.db_instance_class

  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_allocated_storage * 2
  storage_type         = "gp3"
  storage_encrypted     = true

  db_name  = "persistence"
  username = var.db_username
  password = var.db_password

  vpc_security_group_ids = [var.rds_security_group_id]
  db_subnet_group_name   = var.db_subnet_group

  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "mon:04:00-mon:05:00"

  skip_final_snapshot       = !var.enable_deletion_protection
  final_snapshot_identifier = var.enable_deletion_protection ? "${var.project_name}-${var.environment}-persistence-db-final-snapshot" : null
  deletion_protection       = var.enable_deletion_protection

  enabled_cloudwatch_logs_exports = ["error", "general", "slow_query"]

  tags = {
    Name        = "${var.project_name}-${var.environment}-persistence-db"
    Environment = var.environment
    Project     = var.project_name
    Component   = "persistence"
  }
}

# Base de datos para Auth0/Creador de pedido
resource "aws_db_instance" "auth0" {
  identifier     = "${var.project_name}-${var.environment}-auth0-db"
  engine         = "mysql"
  engine_version = "8.0"
  instance_class = var.db_instance_class

  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_allocated_storage * 2
  storage_type         = "gp3"
  storage_encrypted     = true

  db_name  = "auth0_orders"
  username = var.db_username
  password = var.db_password

  vpc_security_group_ids = [var.rds_security_group_id]
  db_subnet_group_name   = var.db_subnet_group

  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "mon:04:00-mon:05:00"

  skip_final_snapshot       = !var.enable_deletion_protection
  final_snapshot_identifier = var.enable_deletion_protection ? "${var.project_name}-${var.environment}-auth0-db-final-snapshot" : null
  deletion_protection       = var.enable_deletion_protection

  enabled_cloudwatch_logs_exports = ["error", "general", "slow_query"]

  tags = {
    Name        = "${var.project_name}-${var.environment}-auth0-db"
    Environment = var.environment
    Project     = var.project_name
    Component   = "auth0"
  }
}

