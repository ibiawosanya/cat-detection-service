#!/bin/bash

# Script to destroy a complete environment
# Usage: ./scripts/destroy-environment.sh <environment> [--force]

set -e

ENVIRONMENT=${1}
FORCE=${2}
AWS_REGION="eu-west-1"
PROJECT_NAME="cat-detection"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

if [ -z "$ENVIRONMENT" ]; then
    echo -e "${RED}❌ Error: Environment parameter required${NC}"
    echo "Usage: $0 <environment> [--force]"
    echo "Example: $0 dev"
    echo "Example: $0 prod --force"
    exit 1
fi

if [ "$ENVIRONMENT" != "dev" ] && [ "$ENVIRONMENT" != "staging" ] && [ "$ENVIRONMENT" != "prod" ]; then
    echo -e "${RED}❌ Error: Environment must be dev, staging, or prod${NC}"
    exit 1
fi

echo -e "${RED}🚨 INFRASTRUCTURE DESTRUCTION WARNING${NC}"
echo "======================================="
echo -e "Environment: ${YELLOW}$ENVIRONMENT${NC}"
echo -e "Region: ${YELLOW}$AWS_REGION${NC}"
echo -e "Timestamp: ${YELLOW}$(date)${NC}"
echo ""

# Extra protection for production
if [ "$ENVIRONMENT" = "prod" ] && [ "$FORCE" != "--force" ]; then
    echo -e "${RED}❌ Production environment requires --force flag${NC}"
    echo "Usage: $0 prod --force"
    exit 1
fi

# Confirmation prompt
echo -e "${YELLOW}⚠️  This will PERMANENTLY DELETE all infrastructure in the $ENVIRONMENT environment!${NC}"
echo ""
echo "This includes:"
echo "• All Lambda functions"
echo "• API Gateway"
echo "• S3 buckets and all data"
echo "• DynamoDB tables and all data"
echo "• CloudFront distributions"
echo "• SQS queues"
echo "• CloudWatch logs and alarms"
echo "• Terraform state bucket"
echo ""
read -p "Type 'DESTROY' to confirm: " CONFIRMATION

if [ "$CONFIRMATION" != "DESTROY" ]; then
    echo -e "${GREEN}✅ Destruction cancelled${NC}"
    exit 0
fi

echo ""
echo -e "${RED}💥 Starting destruction of $ENVIRONMENT environment...${NC}"

# Check if environment exists
TERRAFORM_DIR="terraform/environments/$ENVIRONMENT"
if [ ! -d "$TERRAFORM_DIR" ]; then
    echo -e "${RED}❌ Environment directory not found: $TERRAFORM_DIR${NC}"
    exit 1
fi

if [ ! -f "$TERRAFORM_DIR/backend.tf" ]; then
    echo -e "${YELLOW}⚠️  No backend.tf found. Environment may not be deployed.${NC}"
    echo "Checking for any remaining AWS resources..."
else
    # Destroy Terraform infrastructure
    echo -e "${YELLOW}📝 Initializing Terraform...${NC}"
    cd "$TERRAFORM_DIR"
    terraform init

    echo -e "${YELLOW}📋 Current resources:${NC}"
    terraform state list || echo "No resources found"

    echo -e "${YELLOW}📝 Planning destruction...${NC}"
    terraform plan -destroy -out=destroy.tfplan

    echo -e "${RED}💥 Destroying infrastructure...${NC}"
    terraform apply destroy.tfplan

    echo -e "${GREEN}✅ Terraform resources destroyed${NC}"
    cd ../../../
fi

# Clean up backend resources
if [ -f "$TERRAFORM_DIR/.terraform-backend-config" ]; then
    echo -e "${YELLOW}🧹 Cleaning up Terraform backend...${NC}"
    
    # Source the backend config
    source "$TERRAFORM_DIR/.terraform-backend-config"
    
    echo "S3 Bucket: $TF_BACKEND_BUCKET"
    echo "DynamoDB Table: $TF_BACKEND_DYNAMODB_TABLE"
    
    # Empty and delete S3 bucket
    echo "Emptying S3 bucket..."
    aws s3 rm s3://$TF_BACKEND_BUCKET --recursive --quiet || echo "Bucket already empty"
    
    echo "Deleting S3 bucket..."
    aws s3api delete-bucket --bucket $TF_BACKEND_BUCKET --region $TF_BACKEND_REGION --quiet || echo "Bucket already deleted"
    
    # Delete DynamoDB table
    echo "Deleting DynamoDB table..."
    aws dynamodb delete-table --table-name $TF_BACKEND_DYNAMODB_TABLE --region $TF_BACKEND_REGION --no-cli-pager || echo "Table already deleted"
    
    echo -e "${GREEN}✅ Backend resources cleaned up${NC}"
else
    echo -e "${YELLOW}⚠️  No backend config found, checking for resources manually...${NC}"
    
    # Try to find and clean up any remaining buckets/tables
    echo "Searching for $ENVIRONMENT environment resources..."
    
    # Look for S3 buckets
    S3_BUCKETS=$(aws s3api list-buckets --query "Buckets[?contains(Name, '$PROJECT_NAME') && contains(Name, '$ENVIRONMENT')].Name" --output text)
    if [ -n "$S3_BUCKETS" ]; then
        echo "Found S3 buckets to clean up:"
        for BUCKET in $S3_BUCKETS; do
            echo "  - $BUCKET"
            aws s3 rm s3://$BUCKET --recursive --quiet || true
            aws s3api delete-bucket --bucket $BUCKET --region $AWS_REGION --quiet || true
        done
    fi
    
    # Look for DynamoDB tables
    DYNAMO_TABLES=$(aws dynamodb list-tables --query "TableNames[?contains(@, '$PROJECT_NAME') && contains(@, '$ENVIRONMENT')]" --output text)
    if [ -n "$DYNAMO_TABLES" ]; then
        echo "Found DynamoDB tables to clean up:"
        for TABLE in $DYNAMO_TABLES; do
            echo "  - $TABLE"
            aws dynamodb delete-table --table-name $TABLE --region $AWS_REGION --no-cli-pager || true
        done
    fi
fi

# Clean up local files
echo -e "${YELLOW}🧹 Cleaning up local files...${NC}"
rm -f "$TERRAFORM_DIR/backend.tf"
rm -f "$TERRAFORM_DIR/.terraform-backend-config"
rm -rf "$TERRAFORM_DIR/.terraform/"
rm -f "$TERRAFORM_DIR/destroy.tfplan"

echo ""
echo -e "${GREEN}🎯 DESTRUCTION COMPLETED${NC}"
echo "========================="
echo -e "Environment: ${YELLOW}$ENVIRONMENT${NC}"
echo -e "Status: ${GREEN}✅ DESTROYED${NC}"
echo -e "Timestamp: ${YELLOW}$(date)${NC}"
echo ""
echo -e "${YELLOW}📋 What was destroyed:${NC}"
echo "• All Terraform-managed resources"
echo "• S3 backend bucket and state files"
echo "• DynamoDB state lock table"
echo "• Local Terraform configuration files"
echo ""
echo -e "${GREEN}♻️  Environment can be recreated by:${NC}"
echo "   1. Running: ./scripts/bootstrap-terraform.sh $ENVIRONMENT"
echo "   2. Deploying via normal CI/CD pipeline"
echo ""
echo -e "${GREEN}✅ Destruction completed successfully!${NC}"