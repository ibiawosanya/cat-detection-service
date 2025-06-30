# Random ID for unique bucket names
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# S3 Bucket for Images
resource "aws_s3_bucket" "images" {
  bucket = "${var.environment}-${var.project}-images-${random_id.bucket_suffix.hex}"
  
  tags = {
    Environment = var.environment
    Project     = var.project
  }
}

resource "aws_s3_bucket_versioning" "images" {
  bucket = aws_s3_bucket.images.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "images" {
  bucket = aws_s3_bucket.images.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "images" {
  bucket = aws_s3_bucket.images.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# DynamoDB Table for Results
resource "aws_dynamodb_table" "scan_results" {
  name           = "${var.environment}-${var.project}-scan-results"
  billing_mode   = var.dynamodb_billing_mode
  hash_key       = "scan_id"
  
  # Only set capacity if using PROVISIONED billing
  read_capacity  = var.dynamodb_billing_mode == "PROVISIONED" ? var.dynamodb_read_capacity : null
  write_capacity = var.dynamodb_billing_mode == "PROVISIONED" ? var.dynamodb_write_capacity : null
  
  attribute {
    name = "scan_id"
    type = "S"
  }
  
  attribute {
    name = "user_id"
    type = "S"
  }
  
  attribute {
    name = "created_at"
    type = "S"
  }
  
  global_secondary_index {
    name     = "user-created-index"
    hash_key = "user_id"
    range_key = "created_at"
    
    # Only set capacity if using PROVISIONED billing
    read_capacity  = var.dynamodb_billing_mode == "PROVISIONED" ? var.dynamodb_read_capacity : null
    write_capacity = var.dynamodb_billing_mode == "PROVISIONED" ? var.dynamodb_write_capacity : null
  }
  
  point_in_time_recovery {
    enabled = var.enable_point_in_time_recovery
  }
  
  tags = {
    Environment = var.environment
    Project     = var.project
  }
}

# SQS Queue for Processing
resource "aws_sqs_queue" "processing_queue" {
  name                       = "${var.environment}-${var.project}-processing-queue"
  delay_seconds              = 0
  max_message_size           = 262144
  message_retention_seconds  = var.sqs_message_retention_seconds
  visibility_timeout_seconds = var.sqs_visibility_timeout_seconds
  
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3
  })
  
  tags = {
    Environment = var.environment
    Project     = var.project
  }
}

# Dead Letter Queue
resource "aws_sqs_queue" "dlq" {
  name = "${var.environment}-${var.project}-processing-dlq"
  
  tags = {
    Environment = var.environment
    Project     = var.project
  }
}