#!/bin/bash
set -e

echo "=========================================="
echo "🚀 CampusFix AI - Magic Setup Script"
echo "=========================================="
echo "This script will download Terraform and apply your latest AWS infrastructure."
echo ""

# 1. Ask for credentials
read -p "Enter your AWS Access Key ID: " AWS_ACCESS_KEY_ID
read -s -p "Enter your AWS Secret Access Key: " AWS_SECRET_ACCESS_KEY
echo ""
read -s -p "Enter your Gemini API Key: " GEMINI_API_KEY
echo ""

export AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID
export AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY
export AWS_DEFAULT_REGION="us-east-1"
export TF_VAR_gemini_api_key=$GEMINI_API_KEY

# 2. Download Terraform locally if not present
if [ ! -f "./terraform_bin" ]; then
    echo "Downloading Terraform..."
    wget -q https://releases.hashicorp.com/terraform/1.5.7/terraform_1.5.7_linux_amd64.zip
    mkdir -p tmp_tf
    unzip -q terraform_1.5.7_linux_amd64.zip -d tmp_tf
    mv tmp_tf/terraform ./terraform_bin
    rm -rf tmp_tf terraform_1.5.7_linux_amd64.zip
fi

# 3. Run Terraform
echo "Setting up AWS Infrastructure (this takes ~3-5 minutes)..."
cd terraform
../terraform_bin init
../terraform_bin apply -auto-approve

echo ""
echo "✅ AWS Infrastructure Successfully Updated!"
