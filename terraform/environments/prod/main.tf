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
    bucket = "cat-detection-terraform-state-777"
    key    = "cat-detection/prod/terraform.tfstate"
    region = "eu-west-1"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Environment = "prod"
      Project     = "cat-detection"
      ManagedBy   = "terraform"
    }
  }
}

locals {
  environment = "prod"
  project     = "cat-detection"
}

# Storage Module
module "storage" {
  source = "../../modules/storage"
  
  environment = local.environment
  project     = local.project
  
  # Production-specific overrides
  dynamodb_billing_mode = "PROVISIONED"
  dynamodb_read_capacity = 10
  dynamodb_write_capacity = 10
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
  
  # Production-specific settings
  lambda_memory_size = 1024
  lambda_timeout = 60
  reserved_concurrency = 100
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
  
  # Production-specific API Gateway settings
  throttle_burst_limit = 2000
  throttle_rate_limit = 1000
}

# Web UI Module
module "web_ui" {
  source = "../../modules/web-ui"
  
  environment = local.environment
  project     = local.project
  
  # Production-specific CloudFront settings
  price_class = "PriceClass_All"
  enable_compression = true
}

# Monitoring Module
module "monitoring" {
  source = "../../modules/monitoring"
  
  environment         = local.environment
  project            = local.project
  aws_region         = var.aws_region
  log_retention_days = 30  # Longer retention for prod
  
  lambda_function_names = [
    module.lambda.upload_lambda_function_name,
    module.lambda.process_lambda_function_name,
    module.lambda.status_lambda_function_name
  ]
  
  sqs_queue_name = module.storage.sqs_queue_name
  dynamodb_table_name = module.storage.dynamodb_table_name
  
  # Production alerting
  enable_sns_alerts = true
  alert_email = "ibi.awosanya@gmail.com"
}