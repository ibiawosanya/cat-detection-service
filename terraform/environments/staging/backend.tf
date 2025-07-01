# Auto-generated backend configuration
# Created by bootstrap script on Tue, Jul  1, 2025  4:54:56 AM

terraform {
  backend "s3" {
    bucket         = "cat-detection-terraform-state-staging-9be2c4ef"
    key            = "cat-detection/staging/terraform.tfstate"
    region         = "eu-west-1"
    dynamodb_table = "cat-detection-terraform-locks-staging"
    encrypt        = true
  }
}
