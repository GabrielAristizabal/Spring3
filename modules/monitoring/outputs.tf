output "consistency_log_group_name" {
  description = "Nombre del grupo de logs de consistencia"
  value       = aws_cloudwatch_log_group.consistency.name
}

output "dashboard_url" {
  description = "URL del dashboard de CloudWatch"
  value = "https://${data.aws_region.current.name}.console.aws.amazon.com/cloudwatch/home?region=${data.aws_region.current.name}#dashboards:name=${aws_cloudwatch_dashboard.main.dashboard_name}"
}

data "aws_region" "current" {}

