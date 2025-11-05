output "api_gateway_url" {
  description = "URL del API Gateway"
  value       = aws_apigatewayv2_api.main.api_endpoint
}

output "api_gateway_id" {
  description = "ID del API Gateway"
  value       = aws_apigatewayv2_api.main.id
}

