output "validation_topic_arn" {
  description = "ARN del topic SNS de validación"
  value       = aws_sns_topic.validation.arn
}

output "anomaly_topic_arn" {
  description = "ARN del topic SNS de anomalías"
  value       = aws_sns_topic.anomaly.arn
}

output "audit_topic_arn" {
  description = "ARN del topic SNS de auditoría"
  value       = aws_sns_topic.audit.arn
}

output "order_queue_url" {
  description = "URL de la queue SQS de pedidos"
  value       = aws_sqs_queue.order.url
}

output "order_queue_arn" {
  description = "ARN de la queue SQS de pedidos"
  value       = aws_sqs_queue.order.arn
}

output "validation_queue_url" {
  description = "URL de la queue SQS de validación"
  value       = aws_sqs_queue.validation.url
}

output "validation_queue_arn" {
  description = "ARN de la queue SQS de validación"
  value       = aws_sqs_queue.validation.arn
}

output "anomaly_queue_url" {
  description = "URL de la queue SQS de anomalías"
  value       = aws_sqs_queue.anomaly.url
}

output "anomaly_queue_arn" {
  description = "ARN de la queue SQS de anomalías"
  value       = aws_sqs_queue.anomaly.arn
}

output "validation_dlq_arn" {
  description = "ARN de la Dead Letter Queue de validación"
  value       = aws_sqs_queue.validation_dlq.arn
}

output "anomaly_dlq_arn" {
  description = "ARN de la Dead Letter Queue de anomalías"
  value       = aws_sqs_queue.anomaly_dlq.arn
}

output "order_dlq_arn" {
  description = "ARN de la Dead Letter Queue de pedidos"
  value       = aws_sqs_queue.order_dlq.arn
}

output "validation_dlq_name" {
  description = "Nombre de la Dead Letter Queue de validación"
  value       = aws_sqs_queue.validation_dlq.name
}

output "anomaly_dlq_name" {
  description = "Nombre de la Dead Letter Queue de anomalías"
  value       = aws_sqs_queue.anomaly_dlq.name
}

output "order_dlq_name" {
  description = "Nombre de la Dead Letter Queue de pedidos"
  value       = aws_sqs_queue.order_dlq.name
}

