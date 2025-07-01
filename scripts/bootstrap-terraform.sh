#!/bin/bash

# Bootstrap script to create Terraform S3 backend bucket
# Usage: ./scripts/bootstrap-terraform.sh <environment> <aws-region>

set -e

ENVIRONMENT=${1:-dev}
AWS_REGION=${2:-eu-west-1}
PROJECT_NAME="cat-detection"

echo "🚀 Bootstrapping Terraform backend for environment: $ENVIRONMENT"
echo "📍 Region: $AWS_REGION"

# Generate unique bucket name with random suffix
RANDOM_SUFFIX=$(openssl rand -hex 4)
BUCKET_NAME="${PROJECT_NAME}-terraform-state-${ENVIRONMENT}-${RANDOM_SUFFIX}"
DYNAMODB_TABLE="${PROJECT_NAME}-terraform-locks-${ENVIRONMENT}"

echo "🪣 Creating S3 bucket: $BUCKET_NAME"
echo "🔒 Creating DynamoDB table: $DYNAMODB_TABLE"

# Create S3 bucket for Terraform state
if [ "$AWS_REGION" = "us-east-1" ]; then
    # us-east-1 doesn't need LocationConstraint
    aws s3api create-bucket \
        --bucket "$BUCKET_NAME" \
        --region "$AWS_REGION" \
        --no-cli-pager
else
    # All other regions need LocationConstraint
    aws s3api create-bucket \
        --bucket "$BUCKET_NAME" \
        --region "$AWS_REGION" \
        --create-bucket-configuration LocationConstraint="$AWS_REGION" \
        --no-cli-pager
fi

# Enable versioning on the bucket
aws s3api put-bucket-versioning \
    --bucket "$BUCKET_NAME" \
    --versioning-configuration Status=Enabled \
    --no-cli-pager

# Enable server-side encryption
aws s3api put-bucket-encryption \
    --bucket "$BUCKET_NAME" \
    --server-side-encryption-configuration '{
        "Rules": [
            {
                "ApplyServerSideEncryptionByDefault": {
                    "SSEAlgorithm": "AES256"
                }
            }
        ]
    }' \
    --no-cli-pager

# Block public access - Fixed syntax
aws s3api put-public-access-block \
    --bucket "$BUCKET_NAME" \
    --public-access-block-configuration '{
        "BlockPublicAcls": true,
        "IgnorePublicAcls": true,
        "BlockPublicPolicy": true,
        "RestrictPublicBuckets": true
    }' \
    --no-cli-pager

# Create DynamoDB table for state locking
aws dynamodb create-table \
    --table-name "$DYNAMODB_TABLE" \
    --attribute-definitions AttributeName=LockID,AttributeType=S \
    --key-schema AttributeName=LockID,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region "$AWS_REGION" \
    --no-cli-pager

# Wait for DynamoDB table to be active
echo "⏳ Waiting for DynamoDB table to be active..."
aws dynamodb wait table-exists --table-name "$DYNAMODB_TABLE" --region "$AWS_REGION"

# Create backend configuration file
BACKEND_CONFIG_DIR="terraform/environments/$ENVIRONMENT"
BACKEND_CONFIG_FILE="$BACKEND_CONFIG_DIR/backend.tf"

mkdir -p "$BACKEND_CONFIG_DIR"

cat > "$BACKEND_CONFIG_FILE" << EOF
# Auto-generated backend configuration
# Created by bootstrap script on $(date)

terraform {
  backend "s3" {
    bucket         = "$BUCKET_NAME"
    key            = "cat-detection/$ENVIRONMENT/terraform.tfstate"
    region         = "$AWS_REGION"
    dynamodb_table = "$DYNAMODB_TABLE"
    encrypt        = true
  }
}
EOF

echo "✅ Backend configuration created: $BACKEND_CONFIG_FILE"

# Create environment-specific outputs file for CI/CD
OUTPUTS_FILE="terraform/environments/$ENVIRONMENT/.terraform-backend-config"

cat > "$OUTPUTS_FILE" << EOF
# Terraform backend configuration for $ENVIRONMENT
# Source this file in CI/CD scripts if needed
export TF_BACKEND_BUCKET="$BUCKET_NAME"
export TF_BACKEND_KEY="cat-detection/$ENVIRONMENT/terraform.tfstate"
export TF_BACKEND_REGION="$AWS_REGION"
export TF_BACKEND_DYNAMODB_TABLE="$DYNAMODB_TABLE"
EOF

echo "✅ Environment config created: $OUTPUTS_FILE"

echo ""
echo "🎉 Bootstrap completed successfully!"
echo ""
echo "📋 Summary:"
echo "   S3 Bucket: $BUCKET_NAME"
echo "   DynamoDB Table: $DYNAMODB_TABLE"
echo "   Backend Config: $BACKEND_CONFIG_FILE"
echo ""
echo "▶️  Next steps:"
echo "   1. cd terraform/environments/$ENVIRONMENT"
echo "   2. terraform init"
echo "   3. terraform plan"
echo "   4. terraform apply"
echo ""
echo "🔧 To destroy this environment later:"
echo "   terraform destroy && aws s3 rb s3://$BUCKET_NAME --force && aws dynamodb delete-table --table-name $DYNAMODB_TABLE --region $AWS_REGION"