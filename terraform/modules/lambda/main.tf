# Upload Lambda Function
resource "aws_lambda_function" "upload" {
  filename         = "${path.module}/../../../dist/upload.zip"
  function_name    = "${var.environment}-${var.project}-upload"
  role            = aws_iam_role.lambda_role.arn
  handler         = "handler.upload"
  runtime         = "python3.11"
  timeout         = var.lambda_timeout
  memory_size     = var.lambda_memory_size
  reserved_concurrent_executions = var.reserved_concurrency
  
  environment {
    variables = {
      ENVIRONMENT = var.environment
      S3_BUCKET   = var.s3_bucket_name
      SQS_QUEUE   = var.sqs_queue_url
      DYNAMODB_TABLE = var.dynamodb_table_name
    }
  }
  
  dynamic "tracing_config" {
    for_each = var.enable_x_ray_tracing ? [1] : []
    content {
      mode = "Active"
    }
  }
  
  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic
  ]
  
  tags = {
    Environment = var.environment
    Project     = var.project
  }
}

# Process Lambda Function
resource "aws_lambda_function" "process" {
  filename         = "${path.module}/../../../dist/process.zip"
  function_name    = "${var.environment}-${var.project}-process"
  role            = aws_iam_role.lambda_role.arn
  handler         = "handler.process"
  runtime         = "python3.11"
  timeout         = var.lambda_timeout
  memory_size     = var.lambda_memory_size
  reserved_concurrent_executions = var.reserved_concurrency
  
  environment {
    variables = {
      ENVIRONMENT = var.environment
      DYNAMODB_TABLE = var.dynamodb_table_name
    }
  }
  
  dynamic "tracing_config" {
    for_each = var.enable_x_ray_tracing ? [1] : []
    content {
      mode = "Active"
    }
  }
  
  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic
  ]
  
  tags = {
    Environment = var.environment
    Project     = var.project
  }
}

# Status Check Lambda Function
resource "aws_lambda_function" "status" {
  filename         = "${path.module}/../../../dist/status.zip"
  function_name    = "${var.environment}-${var.project}-status"
  role            = aws_iam_role.lambda_role.arn
  handler         = "handler.status"
  runtime         = "python3.11"
  timeout         = 15  # Status checks should be fast
  memory_size     = 256  # Status checks need less memory
  
  environment {
    variables = {
      ENVIRONMENT = var.environment
      DYNAMODB_TABLE = var.dynamodb_table_name
    }
  }
  
  dynamic "tracing_config" {
    for_each = var.enable_x_ray_tracing ? [1] : []
    content {
      mode = "Active"
    }
  }
  
  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic
  ]
  
  tags = {
    Environment = var.environment
    Project     = var.project
  }
}

# SQS Event Source Mapping
resource "aws_lambda_event_source_mapping" "sqs_processor" {
  event_source_arn = var.sqs_queue_arn
  function_name    = aws_lambda_function.process.arn
  batch_size       = 1
  
  depends_on = [aws_iam_role_policy_attachment.lambda_basic]
}