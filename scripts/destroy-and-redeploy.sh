#!/bin/bash
# destroy-and-redeploy.sh - Complete environment recreation script

set -e

echo "🔄 Cat Detector - Destroy and Redeploy"
echo "======================================"

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/Scripts/activate
    echo "✅ Activated Python virtual environment"
fi

STACK=$(pulumi stack --show-name 2>/dev/null || echo "dev")
echo "📍 Current Stack: $STACK"

# Confirm destruction
echo ""
echo "⚠️  WARNING: This will completely destroy the current infrastructure!"
echo "   - All AWS resources will be deleted"
echo "   - All data will be lost"
echo "   - New URLs will be generated"
echo ""
read -p "Are you sure you want to proceed? (type 'YES' to confirm): " -r
if [[ "$REPLY" != "YES" ]]; then
    echo "Operation cancelled."
    exit 0
fi

# Step 1: Destroy existing infrastructure
echo ""
echo "💥 Step 1: Destroying existing infrastructure..."
pulumi destroy --yes

echo "✅ Infrastructure destroyed successfully!"

# Step 2: Wait a moment for AWS to clean up
echo ""
echo "⏳ Step 2: Waiting for AWS cleanup (30 seconds)..."
sleep 30

# Step 3: Redeploy infrastructure
echo ""
echo "🚀 Step 3: Redeploying infrastructure..."
echo "   This will create new URLs and automatically configure the frontend..."

# Use the enhanced deployment script
./scripts/deploy-pulumi.sh

echo ""
echo "🎉 Destroy and Redeploy Complete!"
echo "=================================="
echo ""
echo "✨ Your Cat Detector has been completely rebuilt with:"
echo "   - New API Gateway URL"
echo "   - New CloudFront distribution URL"
echo "   - Fresh AWS resources"
echo "   - Automatically configured frontend"
echo ""
echo "🧪 Next steps:"
echo "   1. Test the new application"
echo "   2. Run comprehensive tests: ./scripts/test-pulumi.sh"
echo "   3. Update any external references to the new URLs"