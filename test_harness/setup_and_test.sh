#!/bin/bash
# Setup and test script for MCP Test Harness

echo "🔧 MCP Server Test Harness Setup"
echo "================================"

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed"
    echo "Install with: sudo apt install python3-pip"
    exit 1
fi

echo "✅ pip3 found"

# Create virtual environment
echo ""
echo "📦 Setting up virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment exists"
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo ""
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✅ Dependencies installed"

# Check Docker
echo ""
echo "🐳 Checking Docker..."
if command -v docker &> /dev/null; then
    echo "✅ Docker found: $(docker --version)"

    # Check if ramparts:local image exists
    if docker images | grep -q "ramparts.*local"; then
        echo "✅ ramparts:local image found"
    else
        echo "⚠️ ramparts:local image not found"
        echo "   Build with: docker build -t ramparts:local .."
    fi
else
    echo "⚠️ Docker not found (optional for Docker testing)"
fi

# Display usage
echo ""
echo "🚀 Setup complete! You can now run tests:"
echo ""
echo "Test Ramparts Docker image:"
echo "  python test_ramparts.py"
echo ""
echo "Test any MCP server:"
echo "  python mcp_test_harness.py http://localhost:8080"
echo ""
echo "Test Docker container:"
echo "  python mcp_test_harness.py --docker --image ramparts:local"
echo ""
echo "Test multiple servers from config:"
echo "  python mcp_test_harness.py --config example_servers.json"
echo ""
echo "Interactive testing:"
echo "  python mcp_test_harness.py http://localhost:8080 --interactive"

# Optional: Run a quick test
echo ""
read -p "Would you like to run a quick test of the ramparts:local Docker image? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🧪 Running quick test..."
    python test_ramparts.py --mode http
fi