# Auto-generated backend configuration
# Created by bootstrap script on Tue, Jul  1, 2025  4:06:19 AM

terraform {
  backend "s3" {
    bucket         = "cat-detection-terraform-state-prod-51bdc2ca"
    key            = "cat-detection/prod/terraform.tfstate"
    region         = "eu-west-1"
    dynamodb_table = "cat-detection-terraform-locks-prod"
    encrypt        = true
  }
}
