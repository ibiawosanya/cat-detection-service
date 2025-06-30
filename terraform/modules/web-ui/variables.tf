variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "project" {
  description = "Project name"
  type        = string
}

variable "price_class" {
  description = "CloudFront price class"
  type        = string
  default     = "PriceClass_100"
}

variable "enable_compression" {
  description = "Enable CloudFront compression"
  type        = bool
  default     = true
}

variable "default_cache_ttl" {
  description = "Default cache TTL in seconds"
  type        = number
  default     = 3600
}

variable "max_cache_ttl" {
  description = "Maximum cache TTL in seconds"
  type        = number
  default     = 86400
}

variable "enable_logging" {
  description = "Enable CloudFront access logging"
  type        = bool
  default     = false
}

variable "custom_domain" {
  description = "Custom domain name for CloudFront distribution"
  type        = string
  default     = null
}

variable "certificate_arn" {
  description = "ACM certificate ARN for custom domain"
  type        = string
  default     = null
}