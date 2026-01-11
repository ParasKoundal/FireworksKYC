#!/bin/bash

# KYC Identity Verification System - Setup Script
# This script creates a virtual environment and installs all dependencies

set -e  # Exit on any error

echo "============================================================"
echo "KYC Identity Verification System - Setup"
echo "============================================================"
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    echo "Please install Python 3.9 or higher from https://www.python.org/"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.9"

echo "✓ Found Python $PYTHON_VERSION"

# Compare versions (basic check)
if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Error: Python 3.9 or higher is required"
    echo "Current version: $PYTHON_VERSION"
    exit 1
fi

echo ""
echo "Step 1: Creating virtual environment..."
echo "------------------------------------------------------------"

# Create virtual environment
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists"
    read -p "Do you want to recreate it? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing existing virtual environment..."
        rm -rf venv
        python3 -m venv venv
        echo "✓ Virtual environment recreated"
    else
        echo "Using existing virtual environment"
    fi
else
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

echo ""
echo "Step 2: Activating virtual environment..."
echo "------------------------------------------------------------"

# Activate virtual environment
source venv/bin/activate
echo "✓ Virtual environment activated"

echo ""
echo "Step 3: Upgrading pip..."
echo "------------------------------------------------------------"

pip install --upgrade pip > /dev/null 2>&1
echo "✓ pip upgraded to latest version"

echo ""
echo "Step 4: Installing dependencies..."
echo "------------------------------------------------------------"

# Install requirements
pip install -r requirements.txt
echo "✓ All dependencies installed"

echo ""
echo "Step 5: Checking environment configuration..."
echo "------------------------------------------------------------"

# Check for .env file
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "Creating .env file from template..."
        cp .env.example .env
        echo "✓ .env file created"
        echo "⚠️  IMPORTANT: Edit .env file and add your Fireworks API key"
    else
        echo "❌ Warning: .env.example not found"
    fi
else
    echo "✓ .env file already exists"
fi

# Check if API key is set
if [ -f ".env" ]; then
    if grep -q "your_api_key_here" .env; then
        echo "⚠️  WARNING: API key not configured in .env file"
        echo "   Please edit .env and add your Fireworks API key"
    else
        echo "✓ API key appears to be configured"
    fi
fi

echo ""
echo "Step 6: Running setup validation..."
echo "------------------------------------------------------------"

# Run test_setup.py in the virtual environment
source venv/bin/activate && python test_setup.py

echo ""
echo "============================================================"
echo "Setup Complete!"
echo "============================================================"
echo ""
echo "Next steps:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Edit .env file and add your Fireworks API key (if not done)"
echo "  3. Run examples: python example.py"
echo "  4. Process a document: python main.py --image <path>"
echo "  5. Start web UI: streamlit run app.py"
echo ""
echo "Documentation:"
echo "  - Quick Start: QUICKSTART.md"
echo "  - Setup Guide: SETUP_INSTRUCTIONS.md"
echo "  - Full Docs: README.md"
echo ""
echo "To deactivate virtual environment later, run: deactivate"
echo "============================================================"
