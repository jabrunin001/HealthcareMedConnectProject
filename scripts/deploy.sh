#!/bin/bash
# MedConnect deployment script

set -e

# Configuration
ENVIRONMENT=${1:-dev}
REGION=${2:-us-east-1}
STACK_NAME="MedConnectStack"

# Print banner
echo "=================================================="
echo "  MedConnect Deployment Script"
echo "  Environment: $ENVIRONMENT"
echo "  Region: $REGION"
echo "=================================================="

# Check prerequisites
echo "Checking prerequisites..."
command -v aws >/dev/null 2>&1 || { echo "AWS CLI is required but not installed. Aborting."; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "Python 3 is required but not installed. Aborting."; exit 1; }
command -v pip3 >/dev/null 2>&1 || { echo "pip3 is required but not installed. Aborting."; exit 1; }
command -v cdk >/dev/null 2>&1 || { echo "AWS CDK is required but not installed. Aborting."; exit 1; }

# Set environment variables
export ENVIRONMENT=$ENVIRONMENT
export AWS_REGION=$REGION

# Install dependencies
echo "Installing dependencies..."
pip3 install -r requirements.txt

# Install infrastructure dependencies
echo "Installing infrastructure dependencies..."
cd infrastructure
pip3 install -r requirements.txt

# Deploy infrastructure
echo "Deploying infrastructure..."
cdk deploy $STACK_NAME \
  --require-approval never \
  --parameters Environment=$ENVIRONMENT \
  --context environment=$ENVIRONMENT

# Return to root directory
cd ..

echo "Deployment completed successfully!" 