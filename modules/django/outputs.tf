output "ecs_cluster_id" {
  description = "ID del cluster ECS"
  value       = aws_ecs_cluster.main.id
}

output "ecs_service_name" {
  description = "Nombre del servicio ECS"
  value       = aws_ecs_service.django.name
}

output "alb_dns_name" {
  description = "DNS name del Application Load Balancer"
  value       = aws_lb.django.dns_name
}

output "alb_arn" {
  description = "ARN del Application Load Balancer"
  value       = aws_lb.django.arn
}

