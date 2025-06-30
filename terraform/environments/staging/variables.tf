variable "aws_region" {
  description = "AWS region for staging environment"
  type        = string
  default     = "eu-west-1"
}

variable "lambda_memory_size" {
  description = "Memory size for Lambda functions in staging"
  type        = number
  default     = 512
}

variable "lambda_timeout" {
  description = "Timeout for Lambda functions in staging"
  type        = number
  default     = 45
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days for staging"
  type        = number
  default     = 14
}

variable "enable_detailed_monitoring" {
  description = "Enable detailed monitoring for staging"
  type        = bool
  default     = true
}

variable "api_throttle_rate_limit" {
  description = "API Gateway throttle rate limit for staging"
  type        = number
  default     = 200
}

variable "api_throttle_burst_limit" {
  description = "API Gateway throttle burst limit for staging"
  type        = number
  default     = 500
}