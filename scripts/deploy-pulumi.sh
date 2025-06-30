#!/bin/bash
# deploy-pulumi.sh - Enhanced Pulumi deployment script with automatic frontend configuration

set -e

echo "🚀 Cat Detector with Pulumi - Enhanced Deployment"
echo "=================================================="

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/Scripts/activate
    echo "✅ Activated Python virtual environment"
fi

# Get current stack and AWS info
STACK=$(pulumi stack --show-name)
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(pulumi config get aws:region)

echo "📍 Deploying Stack: $STACK"
echo "   AWS Account: $AWS_ACCOUNT"
echo "   AWS Region: $AWS_REGION"

# Show configuration
echo "⚙️  Current Configuration:"
pulumi config

# Preview changes
echo ""
echo "🔍 Previewing infrastructure changes..."
pulumi preview

# Confirm deployment
echo ""
read -p "Deploy these changes? (y/N): " -r
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 0
fi

# Deploy infrastructure
echo "🏗️  Deploying infrastructure..."
pulumi up --yes

# Function to get outputs with retry
get_output_with_retry() {
    local output_name=$1
    local max_attempts=10
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        echo "   Attempt $attempt/$max_attempts: Getting $output_name..."
        local result
        result=$(pulumi stack output $output_name 2>/dev/null || echo "")
        
        if [ -n "$result" ]; then
            echo "$result"
            return 0
        fi
        
        echo "   Waiting 5 seconds before retry..."
        sleep 5
        ((attempt++))
    done
    
    echo ""
    return 1
}

# Get deployment outputs with retry
echo "📝 Getting deployment outputs..."
API_URL=$(get_output_with_retry "api_url")
WEBSITE_URL=$(get_output_with_retry "website_url")
WEB_BUCKET=$(get_output_with_retry "web_bucket")
DISTRIBUTION_ID=$(get_output_with_retry "distribution_id")

# Fallback to constructed values if outputs fail
if [ -z "$API_URL" ] || [ -z "$WEBSITE_URL" ] || [ -z "$WEB_BUCKET" ]; then
    echo "⚠️  Some outputs missing, using fallback construction..."
    
    if [ -z "$API_URL" ]; then
        # Get API Gateway ID
        API_ID=$(aws apigateway get-rest-apis --query "items[?name=='cat-detector-api'].id" --output text 2>/dev/null | head -1)
        if [ -n "$API_ID" ] && [ "$API_ID" != "None" ]; then
            API_URL="https://${API_ID}.execute-api.${AWS_REGION}.amazonaws.com/dev"
        fi
    fi
    
    if [ -z "$WEBSITE_URL" ]; then
        # Get CloudFront distribution
        DISTRIBUTION_DOMAIN=$(aws cloudfront list-distributions --query "DistributionList.Items[?Comment=='cat-detector-web-distribution'].DomainName" --output text 2>/dev/null | head -1)
        if [ -n "$DISTRIBUTION_DOMAIN" ] && [ "$DISTRIBUTION_DOMAIN" != "None" ]; then
            WEBSITE_URL="https://${DISTRIBUTION_DOMAIN}"
        fi
    fi
    
    if [ -z "$WEB_BUCKET" ]; then
        WEB_BUCKET="cat-detector-web-${AWS_ACCOUNT}-${AWS_REGION}"
    fi
    
    if [ -z "$DISTRIBUTION_ID" ]; then
        DISTRIBUTION_ID=$(aws cloudfront list-distributions --query "DistributionList.Items[?Comment=='cat-detector-web-distribution'].Id" --output text 2>/dev/null | head -1)
    fi
fi

# Validate we have required values
if [ -z "$API_URL" ] || [ -z "$WEB_BUCKET" ]; then
    echo "❌ Failed to get required deployment information."
    echo "   API_URL: $API_URL"
    echo "   WEB_BUCKET: $WEB_BUCKET"
    exit 1
fi

echo "✅ Infrastructure deployed successfully!"
echo "   📡 API URL: $API_URL"
echo "   🌐 Website URL: $WEBSITE_URL"
echo "   🪣 Web Bucket: $WEB_BUCKET"

# Update frontend configuration automatically
echo "🔧 Updating frontend configuration..."
if [ -f "src/web/index.html" ]; then
    # Create a backup
    cp src/web/index.html src/web/index.html.backup.$(date +%Y%m%d_%H%M%S)
    
    # Update API URL in the frontend
    if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        # Windows/Git Bash
        sed -i "s|const API_BASE_URL = '.*';|const API_BASE_URL = '${API_URL}';|g" src/web/index.html
    else
        # Linux/macOS
        sed -i.tmp "s|const API_BASE_URL = '.*';|const API_BASE_URL = '${API_URL}';|g" src/web/index.html
        rm -f src/web/index.html.tmp
    fi
    
    echo "✅ Frontend configuration updated with API URL: $API_URL"
else
    echo "⚠️  Frontend file not found. Please check src/web/index.html exists."
    exit 1
fi

# Upload frontend assets
echo "📤 Uploading frontend assets to S3..."
aws s3 sync src/web/ s3://$WEB_BUCKET/ --delete
echo "✅ Frontend uploaded successfully!"

# Invalidate CloudFront cache if we have distribution ID
if [ -n "$DISTRIBUTION_ID" ] && [ "$DISTRIBUTION_ID" != "None" ]; then
    echo "🔄 Invalidating CloudFront cache..."
    aws cloudfront create-invalidation --distribution-id $DISTRIBUTION_ID --paths "/*" > /dev/null
    echo "✅ CloudFront cache invalidated!"
else
    echo "⚠️  CloudFront distribution ID not found, skipping cache invalidation"
fi

# Run basic health check
echo "🩺 Running health check..."
sleep 5  # Wait for deployment to settle

if curl -s "$API_URL/upload" -X OPTIONS > /dev/null 2>&1; then
    echo "✅ API is responding!"
else
    echo "⚠️  API health check failed. Please check logs."
fi

# Test frontend API configuration
echo "🔍 Testing frontend API configuration..."
sleep 10  # Wait for CloudFront invalidation

# Download the deployed frontend and check API URL
DEPLOYED_HTML=$(curl -s "$WEBSITE_URL" 2>/dev/null || echo "")
if [[ "$DEPLOYED_HTML" == *"$API_URL"* ]]; then
    echo "✅ Frontend correctly configured with API URL!"
else
    echo "⚠️  Frontend API configuration may not be updated yet. Please wait and refresh."
fi

# Show final summary
echo ""
echo "🎉 Deployment Complete!"
echo "================================"
echo "📡 API URL: $API_URL"
echo "🌐 Website URL: $WEBSITE_URL"
echo "📊 Stack: $STACK"
echo ""
echo "🧪 Testing commands:"
echo "   ./scripts/test-pulumi.sh                # Run comprehensive tests"
echo "   pytest tests/ -v                       # Run pytest suite"
echo ""
echo "🔧 Useful Pulumi commands:"
echo "   pulumi stack output                     # Show all outputs"
echo "   pulumi logs --follow                    # Follow logs in real-time"
echo "   pulumi destroy                          # Destroy stack resources"
echo ""
echo "📊 Monitoring commands:"
echo "   aws logs tail /aws/lambda/cat-detector-upload-$STACK --follow"
echo "   aws logs tail /aws/lambda/cat-detector-process-$STACK --follow"
echo "   aws logs tail /aws/lambda/cat-detector-status-$STACK --follow"
echo ""
echo "✨ Your Cat Detector is ready!"
echo "   Open: $WEBSITE_URL"