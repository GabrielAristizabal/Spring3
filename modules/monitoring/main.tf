# CloudWatch Log Group para logs de consistencia
resource "aws_cloudwatch_log_group" "consistency" {
  name              = "/aws/lambda/${var.project_name}-${var.environment}-consistency"
  retention_in_days = 30

  tags = {
    Name        = "${var.project_name}-${var.environment}-consistency-logs"
    Environment = var.environment
    Project     = var.project_name
  }
}

# CloudWatch Log Group para logs de validación
resource "aws_cloudwatch_log_group" "validator" {
  name              = "/aws/lambda/${var.validator_function_name}"
  retention_in_days = 30

  tags = {
    Name        = "${var.project_name}-${var.environment}-validator-logs"
    Environment = var.environment
    Project     = var.project_name
  }
}

# CloudWatch Log Group para logs de anomalías
resource "aws_cloudwatch_log_group" "anomaly" {
  name              = "/aws/lambda/${var.anomaly_function_name}"
  retention_in_days = 30

  tags = {
    Name        = "${var.project_name}-${var.environment}-anomaly-logs"
    Environment = var.environment
    Project     = var.project_name
  }
}

# CloudWatch Log Group para logs de sincronización
resource "aws_cloudwatch_log_group" "sync" {
  name              = "/aws/lambda/${var.sync_function_name}"
  retention_in_days = 30

  tags = {
    Name        = "${var.project_name}-${var.environment}-sync-logs"
    Environment = var.environment
    Project     = var.project_name
  }
}

# CloudWatch Log Group para logs de auditoría
resource "aws_cloudwatch_log_group" "audit" {
  name              = "/aws/lambda/${var.audit_function_name}"
  retention_in_days = 30

  tags = {
    Name        = "${var.project_name}-${var.environment}-audit-logs"
    Environment = var.environment
    Project     = var.project_name
  }
}

# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.project_name}-${var.environment}-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/Lambda", "Invocations", { "stat": "Sum", "label": "Validator" }],
            [".", ".", { "stat": "Sum", "label": "Anomaly" }],
            [".", ".", { "stat": "Sum", "label": "Sync" }],
            [".", ".", { "stat": "Sum", "label": "Audit" }]
          ]
          period = 300
          stat   = "Sum"
          region = data.aws_region.current.name
          title  = "Lambda Invocations"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/Lambda", "Errors", { "stat": "Sum", "label": "Validator Errors" }],
            [".", ".", { "stat": "Sum", "label": "Anomaly Errors" }],
            [".", ".", { "stat": "Sum", "label": "Sync Errors" }],
            [".", ".", { "stat": "Sum", "label": "Audit Errors" }]
          ]
          period = 300
          stat   = "Sum"
          region = data.aws_region.current.name
          title  = "Lambda Errors"
        }
      },
      {
        type   = "log"
        x      = 0
        y      = 6
        width  = 24
        height = 6

        properties = {
          query = <<-EOT
            SOURCE '/aws/lambda/${var.validator_function_name}' 
            | fields @timestamp, @message
            | filter @message like /inconsistente/ or @message like /faltante/
            | sort @timestamp desc
            | limit 20
          EOT
          region = data.aws_region.current.name
          title  = "Validator Logs - Inconsistencias Detectadas"
        }
      }
    ]
  })
}

data "aws_region" "current" {}

# CloudWatch Alarms para detección de fallos
resource "aws_cloudwatch_metric_alarm" "validator_errors" {
  alarm_name          = "${var.project_name}-${var.environment}-validator-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Alerta cuando hay errores en el validador de disponibilidad"
  alarm_actions       = []

  dimensions = {
    FunctionName = var.validator_function_name
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-validator-errors-alarm"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_cloudwatch_metric_alarm" "validator_dlq_messages" {
  alarm_name          = "${var.project_name}-${var.environment}-validator-dlq-messages"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Average"
  threshold           = 0
  alarm_description   = "Alerta cuando hay mensajes en DLQ del validador (mensajes fallidos)"
  alarm_actions       = []

  dimensions = {
    QueueName = "${var.project_name}-${var.environment}-validation-dlq"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-validator-dlq-alarm"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_cloudwatch_metric_alarm" "anomaly_dlq_messages" {
  alarm_name          = "${var.project_name}-${var.environment}-anomaly-dlq-messages"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Average"
  threshold           = 0
  alarm_description   = "Alerta cuando hay mensajes en DLQ de anomalías (mensajes fallidos)"
  alarm_actions       = []

  dimensions = {
    QueueName = "${var.project_name}-${var.environment}-anomaly-dlq"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-anomaly-dlq-alarm"
    Environment = var.environment
    Project     = var.project_name
  }
}

