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
  
  # Backend configuration is now in backend.tf (auto-generated)
  # Run ./scripts/bootstrap-terraform.sh dev to create it
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Environment = "dev"
      Project     = "cat-detection"
      ManagedBy   = "terraform"
    }
  }
}

locals {
  environment = "dev"
  project     = "cat-detection"
}

# Storage Module
module "storage" {
  source = "../../modules/storage"
  
  environment = local.environment
  project     = local.project
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
}

# Web UI Module
module "web_ui" {
  source = "../../modules/web-ui"
  
  environment = local.environment
  project     = local.project
}

# Monitoring Module
module "monitoring" {
  source = "../../modules/monitoring"
  
  environment         = local.environment
  project            = local.project
  aws_region         = var.aws_region
  log_retention_days = 7  # Shorter retention for dev
  
  lambda_function_names = [
    module.lambda.upload_lambda_function_name,
    module.lambda.process_lambda_function_name,
    module.lambda.status_lambda_function_name
  ]
  
  sqs_queue_name = module.storage.sqs_queue_name
  dynamodb_table_name = module.storage.dynamodb_table_name
}

# Outputs
output "api_gateway_url" {
  value = module.api_gateway.api_gateway_url
}

output "web_bucket_name" {
  value = module.web_ui.s3_bucket_name
}

output "cloudfront_distribution_id" {
  value = module.web_ui.cloudfront_distribution_id
}

output "web_url" {
  value = module.web_ui.cloudfront_url
}