#!/bin/bash
set -euo pipefail

echo "==============================================="
echo "🚀 Ramparts Codespace Setup Starting..."
echo "==============================================="

# Install Docker
echo "🐳 Installing Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER || true
rm get-docker.sh

# Start Docker
sudo service docker start || true

# Install essential tools
echo "📦 Installing essential build tools..."
sudo apt-get update
sudo apt-get install -y \
    jq \
    curl \
    wget \
    git \
    build-essential \
    pkg-config \
    libssl-dev \
    ca-certificates \
    gnupg \
    lsb-release \
    python3-pip \
    python3-venv

# Install Rust
echo "🦀 Installing Rust..."
if ! command -v rustc &> /dev/null; then
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
fi
source $HOME/.cargo/env || true

# Install Rust components
echo "🦀 Installing Rust components..."
rustup component add rustfmt clippy || true

# Install Python packages
echo "🐍 Installing Python tools..."
pip3 install --user fastmcp pytest httpx pyyaml jsonrpc-websocket || true

# Try to pull Docker images
echo "📥 Pulling Docker images..."
docker pull ghcr.io/shadnygren/ramparts-server:shadnygren-github-actions 2>/dev/null || \
    echo "Note: Could not pull server image"

docker pull ghcr.io/shadnygren/ramparts-mcp:shadnygren-github-actions 2>/dev/null || \
    echo "Note: Could not pull MCP image"

# Tag images for easier use
docker tag ghcr.io/shadnygren/ramparts-server:shadnygren-github-actions ramparts-server:latest 2>/dev/null || true
docker tag ghcr.io/shadnygren/ramparts-mcp:shadnygren-github-actions ramparts-mcp:latest 2>/dev/null || true

# Create test script
cat > test-docker.sh << 'SCRIPT_EOF'
#!/bin/bash
echo "🧪 Testing Ramparts Docker Images..."

# Test server
echo "Testing HTTP server..."
docker run -d --rm --name test-server -p 8080:8080 ramparts-server:latest
sleep 5
curl -s http://localhost:8080/health || echo "Health check"
curl -s -X POST http://localhost:8080/v1/ramparts/scan \
    -H "Content-Type: application/json" \
    -d '{"url": "https://httpbin.org/json"}' | jq . || echo "Scan test"
docker stop test-server 2>/dev/null || true

# Test MCP
echo "Testing MCP image..."
docker run --rm --entrypoint /app/ramparts ramparts-mcp:latest --version
docker run --rm --entrypoint /app/ramparts ramparts-mcp:latest scan https://httpbin.org/json --format json | jq .

echo "✅ Tests complete!"
SCRIPT_EOF
chmod +x test-docker.sh

# Final message
echo ""
echo "==============================================="
echo "✅ Codespace Setup Complete!"
echo "==============================================="
echo ""
echo "Available images:"
docker images | grep ramparts || echo "No images yet - pull manually"
echo ""
echo "Run ./test-docker.sh to test"