#!/bin/bash
# setup-pulumi.sh - Pulumi-specific setup script

set -e  # Exit on any error

echo "��� Cat Detector with Pulumi - Setup"
echo "===================================="

# Check prerequisites
echo "��� Checking prerequisites..."

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install it first."
    echo "   Visit: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9+ first."
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Please run 'aws configure' first."
    exit 1
fi

echo "✅ All prerequisites met!"

# Install Pulumi if not present
if ! command -v pulumi &> /dev/null; then
    echo "��� Installing Pulumi..."
    curl -fsSL https://get.pulumi.com | sh
    export PATH=$PATH:$HOME/.pulumi/bin
    echo "✅ Pulumi installed!"
else
    echo "✅ Pulumi already installed!"
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "��� Setting up Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/Scripts/activate

# Install Python dependencies
echo "��� Installing Python dependencies..."
pip install -r requirements.txt

echo "✅ Dependencies installed!"

# Login to Pulumi
echo "��� Configuring Pulumi backend..."
read -p "Use Pulumi Cloud backend? (y/n, default: n): " -r use_cloud
if [[ $use_cloud == "y" || $use_cloud == "Y" ]]; then
    pulumi login
    echo "✅ Using Pulumi Cloud backend"
else
    pulumi login --local
    echo "✅ Using local Pulumi backend"
fi

# Select or create stack
echo "��� Setting up Pulumi stack..."
read -p "Enter stack name (dev/staging/prod, default: dev): " -r stack_name
stack_name=${stack_name:-dev}

if pulumi stack ls | grep -q "$stack_name"; then
    pulumi stack select "$stack_name"
    echo "✅ Selected existing stack: $stack_name"
else
    pulumi stack init "$stack_name"
    echo "✅ Created new stack: $stack_name"
fi

# Set default configuration
echo "⚙️  Setting default configuration..."
pulumi config set aws:region eu-west-1
pulumi config set cat-detector:environment "$stack_name"

case $stack_name in
    prod)
        pulumi config set cat-detector:lambda-memory 1024
        pulumi config set cat-detector:lambda-timeout 60
        ;;
    staging)
        pulumi config set cat-detector:lambda-memory 768
        pulumi config set cat-detector:lambda-timeout 45
        ;;
    *)
        pulumi config set cat-detector:lambda-memory 512
        pulumi config set cat-detector:lambda-timeout 30
        ;;
esac

echo "✅ Configuration set!"

echo ""
echo "��� Pulumi setup complete! Next steps:"
echo "   1. Run './scripts/deploy-pulumi.sh' to deploy infrastructure"
echo "   2. Use 'pulumi preview' to see changes before deploying"
echo "   3. Use 'pulumi config' to manage environment settings"
echo "   4. Use 'pulumi stack ls' to see all stacks"
