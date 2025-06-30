variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "project" {
  description = "Project name"
  type        = string
}

variable "s3_bucket_name" {
  description = "Name of the S3 bucket for images"
  type        = string
}

variable "s3_bucket_arn" {
  description = "ARN of the S3 bucket for images"
  type        = string
}

variable "sqs_queue_url" {
  description = "URL of the SQS queue"
  type        = string
}

variable "sqs_queue_arn" {
  description = "ARN of the SQS queue"
  type        = string
}

variable "dynamodb_table_name" {
  description = "Name of the DynamoDB table"
  type        = string
}

variable "dynamodb_table_arn" {
  description = "ARN of the DynamoDB table"
  type        = string
}

variable "lambda_memory_size" {
  description = "Memory size for Lambda functions"
  type        = number
  default     = 512
}

variable "lambda_timeout" {
  description = "Timeout for Lambda functions"
  type        = number
  default     = 30
}

variable "reserved_concurrency" {
  description = "Reserved concurrency for Lambda functions"
  type        = number
  default     = null
}

variable "enable_x_ray_tracing" {
  description = "Enable X-Ray tracing for Lambda functions"
  type        = bool
  default     = false
}