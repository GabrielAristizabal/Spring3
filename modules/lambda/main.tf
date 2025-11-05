# IAM Role para Lambda functions
resource "aws_iam_role" "lambda" {
  name = "${var.project_name}-${var.environment}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-${var.environment}-lambda-role"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Policy para acceso a VPC
resource "aws_iam_role_policy_attachment" "lambda_vpc" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

# Policy para CloudWatch Logs
resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Policy personalizada para acceso a RDS, SNS, SQS
resource "aws_iam_role_policy" "lambda_custom" {
  name = "${var.project_name}-${var.environment}-lambda-custom-policy"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "rds:DescribeDBInstances",
          "rds:Connect"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = [
          var.validation_topic_arn,
          var.anomaly_topic_arn,
          var.audit_topic_arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = [
          var.order_queue_arn,
          var.validation_queue_arn,
          var.anomaly_queue_arn,
          var.validation_dlq_arn,
          var.anomaly_dlq_arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# Lambda Layer para MySQL connector
resource "aws_lambda_layer_version" "mysql" {
  filename            = "${path.module}/layers/mysql-layer.zip"
  layer_name          = "${var.project_name}-${var.environment}-mysql-layer"
  compatible_runtimes = ["python3.11", "python3.12"]

  source_code_hash = fileexists("${path.module}/layers/mysql-layer.zip") ? filebase64sha256("${path.module}/layers/mysql-layer.zip") : null
}

# Lambda Function: Crear Pedido
resource "aws_lambda_function" "create_order" {
  filename         = "${path.module}/functions/create_order.zip"
  function_name    = "${var.project_name}-${var.environment}-create-order"
  role            = aws_iam_role.lambda.arn
  handler         = "create_order.lambda_handler"
  runtime         = "python3.11"
  timeout         = 30
  memory_size     = 256

  vpc_config {
    subnet_ids         = var.subnet_ids
    security_group_ids = var.security_group_ids
  }

  environment {
    variables = {
      DB_ENDPOINT = var.db_endpoint
      DB_NAME     = var.db_name
      DB_USERNAME = var.db_username
      DB_PASSWORD = var.db_password
      ORDER_QUEUE_URL = var.order_queue_url
      VALIDATION_QUEUE_URL = var.validation_queue_url
    }
  }

  layers = [aws_lambda_layer_version.mysql.arn]

  source_code_hash = fileexists("${path.module}/functions/create_order.zip") ? filebase64sha256("${path.module}/functions/create_order.zip") : null

  tags = {
    Name        = "${var.project_name}-${var.environment}-create-order"
    Environment = var.environment
    Project     = var.project_name
    Component   = "order_creation"
  }
}

# Lambda Function: Validador de Disponibilidad (CRÍTICO para detección 100%)
resource "aws_lambda_function" "validator" {
  filename         = "${path.module}/functions/validator.zip"
  function_name    = "${var.project_name}-${var.environment}-validator"
  role            = aws_iam_role.lambda.arn
  handler         = "validator.lambda_handler"
  runtime         = "python3.11"
  timeout         = 60
  memory_size     = 512

  vpc_config {
    subnet_ids         = var.subnet_ids
    security_group_ids = var.security_group_ids
  }

  environment {
    variables = {
      DB_ENDPOINT = var.db_endpoint
      DB_NAME     = var.db_name
      DB_USERNAME = var.db_username
      DB_PASSWORD = var.db_password
      PERSISTENCE_DB_ENDPOINT = var.persistence_db_endpoint
      PERSISTENCE_DB_NAME = var.persistence_db_name
      VALIDATION_TOPIC_ARN = var.validation_topic_arn
      ANOMALY_QUEUE_URL = var.anomaly_queue_url
      VALIDATION_QUEUE_ARN = var.validation_queue_arn
    }
  }

  layers = [aws_lambda_layer_version.mysql.arn]

  source_code_hash = fileexists("${path.module}/functions/validator.zip") ? filebase64sha256("${path.module}/functions/validator.zip") : null

  # Dead Letter Queue para garantizar que ningún mensaje se pierda
  dead_letter_config {
    target_arn = var.validation_dlq_arn
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-validator"
    Environment = var.environment
    Project     = var.project_name
    Component   = "availability_validator"
  }
}


# Event Source Mapping: SQS Queue -> Validator Lambda
# Este mapping conecta la cola de validación con la función Lambda validador
# para garantizar que todos los mensajes se procesen
resource "aws_lambda_event_source_mapping" "validator_queue" {
  event_source_arn                   = var.validation_queue_arn
  function_name                      = aws_lambda_function.validator.arn
  batch_size                         = 1
  maximum_batching_window_in_seconds = 0
  enabled                            = true

  # Configuración para garantizar procesamiento
  function_response_types = []
}

# Lambda Function: Gestor de Anomalías
resource "aws_lambda_function" "anomaly" {
  filename         = "${path.module}/functions/anomaly.zip"
  function_name    = "${var.project_name}-${var.environment}-anomaly"
  role            = aws_iam_role.lambda.arn
  handler         = "anomaly.lambda_handler"
  runtime         = "python3.11"
  timeout         = 30
  memory_size     = 256

  vpc_config {
    subnet_ids         = var.subnet_ids
    security_group_ids = var.security_group_ids
  }

  environment {
    variables = {
      DB_ENDPOINT = var.db_endpoint
      DB_NAME     = var.db_name
      ANOMALY_TOPIC_ARN = var.anomaly_topic_arn
      AUDIT_TOPIC_ARN = var.audit_topic_arn
    }
  }

  layers = [aws_lambda_layer_version.mysql.arn]

  source_code_hash = fileexists("${path.module}/functions/anomaly.zip") ? filebase64sha256("${path.module}/functions/anomaly.zip") : null

  dead_letter_config {
    target_arn = var.anomaly_dlq_arn
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-anomaly"
    Environment = var.environment
    Project     = var.project_name
    Component   = "anomaly_manager"
  }
}

# Event Source Mapping: SQS Queue -> Anomaly Lambda
# Este mapping conecta la cola de anomalías con la función Lambda gestor de anomalías
resource "aws_lambda_event_source_mapping" "anomaly_queue" {
  event_source_arn                   = var.anomaly_queue_arn
  function_name                      = aws_lambda_function.anomaly.arn
  batch_size                         = 1
  maximum_batching_window_in_seconds = 0
  enabled                            = true

  function_response_types = []
}

# Lambda Function: Sincronizador de Estado
resource "aws_lambda_function" "sync" {
  filename         = "${path.module}/functions/sync.zip"
  function_name    = "${var.project_name}-${var.environment}-sync"
  role            = aws_iam_role.lambda.arn
  handler         = "sync.lambda_handler"
  runtime         = "python3.11"
  timeout         = 30
  memory_size     = 256

  vpc_config {
    subnet_ids         = var.subnet_ids
    security_group_ids = var.security_group_ids
  }

  environment {
    variables = {
      DB_ENDPOINT = var.db_endpoint
      DB_NAME     = var.db_name
      DB_USERNAME = var.db_username
      DB_PASSWORD = var.db_password
    }
  }

  layers = [aws_lambda_layer_version.mysql.arn]

  source_code_hash = fileexists("${path.module}/functions/sync.zip") ? filebase64sha256("${path.module}/functions/sync.zip") : null

  tags = {
    Name        = "${var.project_name}-${var.environment}-sync"
    Environment = var.environment
    Project     = var.project_name
    Component   = "state_synchronizer"
  }
}

# Lambda Function: Emisor de Auditoría
resource "aws_lambda_function" "audit" {
  filename         = "${path.module}/functions/audit.zip"
  function_name    = "${var.project_name}-${var.environment}-audit"
  role            = aws_iam_role.lambda.arn
  handler         = "audit.lambda_handler"
  runtime         = "python3.11"
  timeout         = 30
  memory_size     = 256

  environment {
    variables = {
      DB_ENDPOINT = var.db_endpoint
      DB_NAME     = var.db_name
      DB_USERNAME = var.db_username
      DB_PASSWORD = var.db_password
      AUDIT_TOPIC_ARN = var.audit_topic_arn
    }
  }

  layers = [aws_lambda_layer_version.mysql.arn]

  source_code_hash = fileexists("${path.module}/functions/audit.zip") ? filebase64sha256("${path.module}/functions/audit.zip") : null

  tags = {
    Name        = "${var.project_name}-${var.environment}-audit"
    Environment = var.environment
    Project     = var.project_name
    Component   = "audit_emitter"
  }
}

# Lambda Function: Verificar Consistencia (para experimento)
resource "aws_lambda_function" "check_consistency" {
  filename         = "${path.module}/functions/check_consistency.zip"
  function_name    = "${var.project_name}-${var.environment}-check-consistency"
  role            = aws_iam_role.lambda.arn
  handler         = "check_consistency.lambda_handler"
  runtime         = "python3.11"
  timeout         = 60
  memory_size     = 512

  vpc_config {
    subnet_ids         = var.subnet_ids
    security_group_ids = var.security_group_ids
  }

  environment {
    variables = {
      DB_ENDPOINT = var.db_endpoint
      DB_NAME     = var.db_name
      DB_USERNAME = var.db_username
      DB_PASSWORD = var.db_password
      PERSISTENCE_DB_ENDPOINT = var.db_endpoint
    }
  }

  layers = [aws_lambda_layer_version.mysql.arn]

  source_code_hash = fileexists("${path.module}/functions/check_consistency.zip") ? filebase64sha256("${path.module}/functions/check_consistency.zip") : null

  tags = {
    Name        = "${var.project_name}-${var.environment}-check-consistency"
    Environment = var.environment
    Project     = var.project_name
    Component   = "consistency_checker"
  }
}

# SNS Subscription: Validación -> Anomaly Queue
resource "aws_sns_topic_subscription" "validation_to_anomaly" {
  topic_arn = var.validation_topic_arn
  protocol  = "sqs"
  endpoint  = var.anomaly_queue_arn
}

# SNS Subscription: Anomalía Consistente -> Sync Lambda
resource "aws_sns_topic_subscription" "anomaly_consistent_to_sync" {
  topic_arn = var.anomaly_topic_arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.sync.arn
  filter_policy = jsonencode({
    resultado = ["Consistente"]
  })
}

# SNS Subscription: Anomalía No Consistente -> Audit Lambda
resource "aws_sns_topic_subscription" "anomaly_inconsistent_to_audit" {
  topic_arn = var.anomaly_topic_arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.audit.arn
  filter_policy = jsonencode({
    resultado = ["No consistente"]
  })
}

# Permission para que SNS invoque Sync Lambda
resource "aws_lambda_permission" "sns_sync" {
  statement_id  = "AllowExecutionFromSNS"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.sync.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = var.anomaly_topic_arn
}

# Permission para que SNS invoque Audit Lambda
resource "aws_lambda_permission" "sns_audit" {
  statement_id  = "AllowExecutionFromSNS"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.audit.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = var.anomaly_topic_arn
}

