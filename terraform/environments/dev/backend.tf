terraform {
  backend "s3" {
    bucket         = "cat-detection-terraform-state-dev-92af823f"
    key            = "cat-detection/dev/terraform.tfstate"
    region         = "eu-west-1"
    dynamodb_table = "cat-detection-terraform-locks-dev"
    encrypt        = true
  }
}
