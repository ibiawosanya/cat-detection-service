variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "project" {
  description = "Project name"
  type        = string
}

variable "upload_lambda_invoke_arn" {
  description = "Invoke ARN of the upload Lambda function"
  type        = string
}

variable "status_lambda_invoke_arn" {
  description = "Invoke ARN of the status Lambda function"
  type        = string
}

variable "upload_lambda_function_name" {
  description = "Name of the upload Lambda function"
  type        = string
}

variable "status_lambda_function_name" {
  description = "Name of the status Lambda function"
  type        = string
}

variable "throttle_rate_limit" {
  description = "API Gateway throttle rate limit"
  type        = number
  default     = 100
}

variable "throttle_burst_limit" {
  description = "API Gateway throttle burst limit"
  type        = number
  default     = 200
}

variable "enable_api_key" {
  description = "Enable API key requirement"
  type        = bool
  default     = false
}

variable "cors_allow_origins" {
  description = "CORS allowed origins"
  type        = list(string)
  default     = ["*"]
}