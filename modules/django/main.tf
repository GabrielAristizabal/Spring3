# CloudWatch Log Group para Django
resource "aws_cloudwatch_log_group" "django" {
  name              = "/ecs/${var.project_name}-${var.environment}-django"
  retention_in_days = 7

  tags = {
    Name        = "${var.project_name}-${var.environment}-django-logs"
    Environment = var.environment
    Project     = var.project_name
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-${var.environment}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-cluster"
    Environment = var.environment
    Project     = var.project_name
  }
}

# IAM Role para ECS Task Execution
resource "aws_iam_role" "ecs_execution" {
  name = "${var.project_name}-${var.environment}-ecs-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-${var.environment}-ecs-execution-role"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_iam_role_policy_attachment" "ecs_execution" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# IAM Role para ECS Task
resource "aws_iam_role" "ecs_task" {
  name = "${var.project_name}-${var.environment}-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-${var.environment}-ecs-task-role"
    Environment = var.environment
    Project     = var.project_name
  }
}

# ECS Task Definition
resource "aws_ecs_task_definition" "django" {
  family                   = "${var.project_name}-${var.environment}-django"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.django_cpu
  memory                   = var.django_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "django"
      image     = var.django_image
      essential = true

      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "DB_ENDPOINT"
          value = var.db_endpoint
        },
        {
          name  = "DB_NAME"
          value = var.db_name
        },
        {
          name  = "DB_USERNAME"
          value = var.db_username
        },
        {
          name  = "DB_PASSWORD"
          value = var.db_password
        },
        {
          name  = "PERSISTENCE_DB_ENDPOINT"
          value = var.persistence_db_endpoint
        },
        {
          name  = "PERSISTENCE_DB_NAME"
          value = var.persistence_db_name
        },
        {
          name  = "VALIDATOR_FUNCTION_ARN"
          value = var.validation_function_arn
        },
        {
          name  = "ANOMALY_FUNCTION_ARN"
          value = var.anomaly_function_arn
        },
        {
          name  = "CLOUDWATCH_LOG_GROUP"
          value = var.cloudwatch_log_group
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.django.name
          "awslogs-region"        = data.aws_region.current.name
          "awslogs-stream-prefix" = "ecs"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])

  tags = {
    Name        = "${var.project_name}-${var.environment}-django-task"
    Environment = var.environment
    Project     = var.project_name
  }
}

data "aws_region" "current" {}

# ECS Service
resource "aws_ecs_service" "django" {
  name            = "${var.project_name}-${var.environment}-django-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.django.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.subnet_ids
    security_groups  = var.security_group_ids
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.django.arn
    container_name  = "django"
    container_port  = 8000
  }

  depends_on = [aws_lb_listener.django]

  tags = {
    Name        = "${var.project_name}-${var.environment}-django-service"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Application Load Balancer
resource "aws_lb" "django" {
  name               = "s3-${var.environment}-django-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = var.security_group_ids
  subnets            = var.subnet_ids

  enable_deletion_protection = false

  tags = {
    Name        = "${var.project_name}-${var.environment}-django-alb"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Target Group
resource "aws_lb_target_group" "django" {
  name        = "s3-${var.environment}-django-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = "/health"
    protocol            = "HTTP"
    matcher             = "200"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-django-tg"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Listener
resource "aws_lb_listener" "django" {
  load_balancer_arn = aws_lb.django.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.django.arn
  }
}

