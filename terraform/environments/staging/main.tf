terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }
  
  backend "s3" {
    bucket = "cat-detection-terraform-state-20250630-666cdc8a"
    key    = "cat-detection/staging/terraform.tfstate"
    region = "eu-west-1"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Environment = "staging"
      Project     = "cat-detection"
      ManagedBy   = "terraform"
    }
  }
}

locals {
  environment = "staging"
  project     = "cat-detection"
}

# Storage Module
module "storage" {
  source = "../../modules/storage"
  
  environment = local.environment
  project     = local.project
  
  # Staging-specific configurations
  dynamodb_billing_mode = "PAY_PER_REQUEST"  # More cost-effective for staging
}

# Lambda Module
module "lambda" {
  source = "../../modules/lambda"
  
  environment          = local.environment
  project             = local.project
  s3_bucket_name      = module.storage.s3_bucket_name
  s3_bucket_arn       = module.storage.s3_bucket_arn
  sqs_queue_url       = module.storage.sqs_queue_url
  sqs_queue_arn       = module.storage.sqs_queue_arn
  dynamodb_table_name = module.storage.dynamodb_table_name
  dynamodb_table_arn  = module.storage.dynamodb_table_arn
  
  # Staging-specific Lambda settings
  lambda_memory_size = 512   # Balanced performance for staging
  lambda_timeout = 45        # Reasonable timeout for staging
  reserved_concurrency = 20  # Limited concurrency for cost control
}

# API Gateway Module
module "api_gateway" {
  source = "../../modules/api-gateway"
  
  environment = local.environment
  project     = local.project
  
  upload_lambda_invoke_arn = module.lambda.upload_lambda_invoke_arn
  status_lambda_invoke_arn = module.lambda.status_lambda_invoke_arn
  upload_lambda_function_name = module.lambda.upload_lambda_function_name
  status_lambda_function_name = module.lambda.status_lambda_function_name
  
  # Staging-specific API Gateway settings
  throttle_burst_limit = 500
  throttle_rate_limit = 200
}

# Web UI Module
module "web_ui" {
  source = "../../modules/web-ui"
  
  environment = local.environment
  project     = local.project
  
  # Staging-specific CloudFront settings
  price_class = "PriceClass_100"  # Use only North America and Europe
  enable_compression = true
}

# Monitoring Module
module "monitoring" {
  source = "../../modules/monitoring"
  
  environment         = local.environment
  project            = local.project
  aws_region         = var.aws_region
  log_retention_days = 14  # Moderate retention for staging
  
  lambda_function_names = [
    module.lambda.upload_lambda_function_name,
    module.lambda.process_lambda_function_name,
    module.lambda.status_lambda_function_name
  ]
  
  sqs_queue_name = module.storage.sqs_queue_name
  dynamodb_table_name = module.storage.dynamodb_table_name
  
  # Staging alerting (less aggressive than prod)
  enable_sns_alerts = true
  alert_email = "ibi.awosanya@gmail.com"
}

# Outputs
output "api_gateway_url" {
  value = module.api_gateway.api_gateway_url
  description = "API Gateway URL for staging environment"
}

output "web_bucket_name" {
  value = module.web_ui.s3_bucket_name
  description = "S3 bucket name for web UI"
}

output "cloudfront_distribution_id" {
  value = module.web_ui.cloudfront_distribution_id
  description = "CloudFront distribution ID"
}

output "web_url" {
  value = module.web_ui.cloudfront_url
  description = "Web UI URL"
}

output "monitoring_dashboard_url" {
  value = module.monitoring.dashboard_url
  description = "CloudWatch dashboard URL"
}