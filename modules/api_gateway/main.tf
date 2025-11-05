# API Gateway REST API
resource "aws_apigatewayv2_api" "main" {
  name          = "${var.project_name}-${var.environment}-api"
  protocol_type = "HTTP"
  description   = "API Gateway para sistema de pedidos"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers = ["*"]
    max_age       = 300
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-api"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Integration para crear pedido
resource "aws_apigatewayv2_integration" "create_order" {
  api_id = aws_apigatewayv2_api.main.id

  integration_uri    = var.create_order_function_arn
  integration_type   = "AWS_PROXY"
  integration_method = "POST"
}

# Integration para verificar consistencia
resource "aws_apigatewayv2_integration" "check_consistency" {
  api_id = aws_apigatewayv2_api.main.id

  integration_uri    = var.check_consistency_function_arn
  integration_type   = "AWS_PROXY"
  integration_method = "POST"
}

# Route: POST /pedidos
resource "aws_apigatewayv2_route" "create_order" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /pedidos"
  target    = "integrations/${aws_apigatewayv2_integration.create_order.id}"
}

# Route: POST /pedidos/{pedido_id}/verificar-consistencia
resource "aws_apigatewayv2_route" "check_consistency" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /pedidos/{pedido_id}/verificar-consistencia"
  target    = "integrations/${aws_apigatewayv2_integration.check_consistency.id}"
}

# Stage
resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = "$default"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      routeKey       = "$context.routeKey"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
    })
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-api-stage"
    Environment = var.environment
    Project     = var.project_name
  }
}

# CloudWatch Log Group para API Gateway
resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/aws/apigateway/${var.project_name}-${var.environment}"
  retention_in_days = 7

  tags = {
    Name        = "${var.project_name}-${var.environment}-api-gateway-logs"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Permission para que API Gateway invoque Lambda
resource "aws_lambda_permission" "api_create_order" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.create_order_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_check_consistency" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.check_consistency_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

