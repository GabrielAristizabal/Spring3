output "app_public_ip" {
  value = aws_instance.app.public_ip
}

output "rds_address" {
  value = aws_db_instance.postgres.address
}

output "kms_key_arn_out" {
  value = aws_kms_key.wms.arn
}

output "cloudwatch_log_group" {
  value = aws_cloudwatch_log_group.app_logs.name
}
