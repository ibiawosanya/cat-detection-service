#!/bin/bash

set -e

ENVIRONMENT=${1:-dev}
AWS_REGION=${2:-eu-west-1}

echo "Deploying to environment: $ENVIRONMENT"

# Build Lambda packages
echo "Building Lambda packages..."
mkdir -p dist

build_lambda() {
    local lambda_name=$1
    echo "Building $lambda_name lambda..."
    
    cd src/lambdas/$lambda_name
    
    # Create virtual environment
    python3 -m venv venv
    source venv/bin/activate
    
    # Install dependencies
    pip install -r requirements.txt -t .
    
    # Create zip package
    zip -r ../../../dist/$lambda_name.zip . -x "venv/*" "*.pyc" "__pycache__/*"
    
    # Cleanup
    deactivate
    rm -rf venv
    
    cd ../../..
}

build_lambda "upload"
build_lambda "process"
build_lambda "status"

# Deploy infrastructure
echo "Deploying infrastructure..."
cd terraform/environments/$ENVIRONMENT

terraform init
terraform plan
terraform apply -auto-approve

# Get outputs
API_URL=$(terraform output -raw api_gateway_url)
WEB_BUCKET=$(terraform output -raw web_bucket_name)
CLOUDFRONT_ID=$(terraform output -raw cloudfront_distribution_id)

cd ../../..

# Build and deploy web UI
echo "Building and deploying web UI..."
cd src/web-ui

npm install
REACT_APP_API_URL=$API_URL npm run build

# Deploy to S3
aws s3 sync build/ s3://$WEB_BUCKET --delete --region $AWS_REGION

# Invalidate CloudFront
aws cloudfront create-invalidation --distribution-id $CLOUDFRONT_ID --paths "/*"

cd ../..

echo "Deployment complete!"
echo "API URL: $API_URL"
echo "Web URL: https://$(aws cloudfront get-distribution --id $CLOUDFRONT_ID --query 'Distribution.DomainName' --output text)"