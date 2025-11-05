output "create_order_function_arn" {
  description = "ARN de la función Lambda crear pedido"
  value       = aws_lambda_function.create_order.arn
}

output "create_order_function_name" {
  description = "Nombre de la función Lambda crear pedido"
  value       = aws_lambda_function.create_order.function_name
}

output "validator_function_arn" {
  description = "ARN de la función Lambda validador"
  value       = aws_lambda_function.validator.arn
}

output "validator_function_name" {
  description = "Nombre de la función Lambda validador"
  value       = aws_lambda_function.validator.function_name
}

output "anomaly_function_arn" {
  description = "ARN de la función Lambda gestor de anomalías"
  value       = aws_lambda_function.anomaly.arn
}

output "anomaly_function_name" {
  description = "Nombre de la función Lambda gestor de anomalías"
  value       = aws_lambda_function.anomaly.function_name
}

output "sync_function_arn" {
  description = "ARN de la función Lambda sincronizador"
  value       = aws_lambda_function.sync.arn
}

output "sync_function_name" {
  description = "Nombre de la función Lambda sincronizador"
  value       = aws_lambda_function.sync.function_name
}

output "audit_function_arn" {
  description = "ARN de la función Lambda auditoría"
  value       = aws_lambda_function.audit.arn
}

output "audit_function_name" {
  description = "Nombre de la función Lambda auditoría"
  value       = aws_lambda_function.audit.function_name
}

output "check_consistency_function_arn" {
  description = "ARN de la función Lambda verificar consistencia"
  value       = aws_lambda_function.check_consistency.arn
}

output "check_consistency_function_name" {
  description = "Nombre de la función Lambda verificar consistencia"
  value       = aws_lambda_function.check_consistency.function_name
}

