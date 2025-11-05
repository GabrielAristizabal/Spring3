# SNS Topic para validación de disponibilidad
resource "aws_sns_topic" "validation" {
  name = "${var.project_name}-${var.environment}-validation-topic"

  tags = {
    Name        = "${var.project_name}-${var.environment}-validation-topic"
    Environment = var.environment
    Project     = var.project_name
  }
}

# SNS Topic para anomalías
resource "aws_sns_topic" "anomaly" {
  name = "${var.project_name}-${var.environment}-anomaly-topic"

  tags = {
    Name        = "${var.project_name}-${var.environment}-anomaly-topic"
    Environment = var.environment
    Project     = var.project_name
  }
}

# SNS Topic para auditoría
resource "aws_sns_topic" "audit" {
  name = "${var.project_name}-${var.environment}-audit-topic"

  tags = {
    Name        = "${var.project_name}-${var.environment}-audit-topic"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Dead Letter Queue para pedidos
resource "aws_sqs_queue" "order_dlq" {
  name                      = "${var.project_name}-${var.environment}-order-dlq"
  message_retention_seconds = 1209600 # 14 días

  tags = {
    Name        = "${var.project_name}-${var.environment}-order-dlq"
    Environment = var.environment
    Project     = var.project_name
  }
}

# SQS Queue para pedidos
resource "aws_sqs_queue" "order" {
  name                      = "${var.project_name}-${var.environment}-order-queue"
  message_retention_seconds = 345600 # 4 días
  visibility_timeout_seconds = 60

  tags = {
    Name        = "${var.project_name}-${var.environment}-order-queue"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Configurar redrive policy para order queue
resource "aws_sqs_queue_redrive_policy" "order" {
  queue_url = aws_sqs_queue.order.id
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.order_dlq.arn
    maxReceiveCount     = 3
  })
}

# SQS Queue para validación
resource "aws_sqs_queue" "validation" {
  name                      = "${var.project_name}-${var.environment}-validation-queue"
  message_retention_seconds = 345600 # 4 días
  visibility_timeout_seconds = 120

  tags = {
    Name        = "${var.project_name}-${var.environment}-validation-queue"
    Environment = var.environment
    Project     = var.project_name
  }
}

# SQS Queue para anomalías
resource "aws_sqs_queue" "anomaly" {
  name                      = "${var.project_name}-${var.environment}-anomaly-queue"
  message_retention_seconds = 345600 # 4 días
  visibility_timeout_seconds = 60

  tags = {
    Name        = "${var.project_name}-${var.environment}-anomaly-queue"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Dead Letter Queue para validación
resource "aws_sqs_queue" "validation_dlq" {
  name                      = "${var.project_name}-${var.environment}-validation-dlq"
  message_retention_seconds = 1209600 # 14 días

  tags = {
    Name        = "${var.project_name}-${var.environment}-validation-dlq"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Configurar redrive policy para validación queue
resource "aws_sqs_queue_redrive_policy" "validation" {
  queue_url = aws_sqs_queue.validation.id
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.validation_dlq.arn
    maxReceiveCount     = 3
  })
}

# Dead Letter Queue para anomalías
resource "aws_sqs_queue" "anomaly_dlq" {
  name                      = "${var.project_name}-${var.environment}-anomaly-dlq"
  message_retention_seconds = 1209600 # 14 días

  tags = {
    Name        = "${var.project_name}-${var.environment}-anomaly-dlq"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Configurar redrive policy para anomaly queue
resource "aws_sqs_queue_redrive_policy" "anomaly" {
  queue_url = aws_sqs_queue.anomaly.id
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.anomaly_dlq.arn
    maxReceiveCount     = 3
  })
}

