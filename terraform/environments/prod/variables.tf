variable "aws_region" {
  description = "AWS region for production environment"
  type        = string
  default     = "eu-west-1"
}

variable "lambda_memory_size" {
  description = "Memory size for Lambda functions in production"
  type        = number
  default     = 1024
}

variable "lambda_timeout" {
  description = "Timeout for Lambda functions in production"
  type        = number
  default     = 60
}

variable "reserved_concurrency" {
  description = "Reserved concurrency for Lambda functions in production"
  type        = number
  default     = 100
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days for production"
  type        = number
  default     = 30
}

variable "enable_detailed_monitoring" {
  description = "Enable detailed monitoring for production"
  type        = bool
  default     = true
}

variable "enable_sns_alerts" {
  description = "Enable SNS alerts for production"
  type        = bool
  default     = true
}

variable "alert_email" {
  description = "Email address for production alerts"
  type        = string
  default     = "ibi.awosanya@gmail.com"
}

variable "api_throttle_rate_limit" {
  description = "API Gateway throttle rate limit for production"
  type        = number
  default     = 1000
}

variable "api_throttle_burst_limit" {
  description = "API Gateway throttle burst limit for production"
  type        = number
  default     = 2000
}

variable "dynamodb_read_capacity" {
  description = "DynamoDB read capacity units for production"
  type        = number
  default     = 10
}

variable "dynamodb_write_capacity" {
  description = "DynamoDB write capacity units for production"
  type        = number
  default     = 10
}

variable "enable_backup" {
  description = "Enable automatic backups for production"
  type        = bool
  default     = true
}

variable "backup_retention_days" {
  description = "Backup retention in days for production"
  type        = number
  default     = 35
}

variable "cloudfront_price_class" {
  description = "CloudFront price class for production"
  type        = string
  default     = "PriceClass_All"
}