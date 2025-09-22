#!/bin/bash
set -e

echo "🚀 Setting up Ramparts development environment..."

# Install Rust toolchain and components
echo "📦 Installing Rust toolchain..."
rustup component add rustfmt clippy
rustup update

# Install cargo tools
echo "📦 Installing cargo tools..."
cargo install cargo-watch cargo-edit || true

# Install Python testing dependencies
echo "🐍 Installing Python testing tools..."
pip3 install --user fastmcp pytest httpx pyyaml

# Build the project to cache dependencies
echo "🔨 Building Ramparts..."
cargo build --all-features || echo "Note: Build may fail due to missing dependencies, continuing..."

# Login to GitHub Container Registry
echo "🔐 Logging into GitHub Container Registry..."
echo "$GITHUB_TOKEN" | docker login ghcr.io -u "$GITHUB_USER" --password-stdin || echo "Note: GHCR login failed, images may not be accessible"

# Pull the pre-built Docker images
echo "📥 Pulling Ramparts Docker images..."
BRANCH_NAME=$(git branch --show-current || echo "main")

# Try to pull images for current branch
docker pull ghcr.io/shadnygren/ramparts-server:${BRANCH_NAME} 2>/dev/null || \
  docker pull ghcr.io/shadnygren/ramparts-server:shadnygren-github-actions 2>/dev/null || \
  docker pull ghcr.io/shadnygren/ramparts-server:latest 2>/dev/null || \
  echo "Note: Could not pull server image"

docker pull ghcr.io/shadnygren/ramparts-mcp:${BRANCH_NAME} 2>/dev/null || \
  docker pull ghcr.io/shadnygren/ramparts-mcp:shadnygren-github-actions 2>/dev/null || \
  docker pull ghcr.io/shadnygren/ramparts-mcp:latest 2>/dev/null || \
  echo "Note: Could not pull MCP image"

# Create test script
cat > test-ramparts.sh << 'EOF'
#!/bin/bash
echo "🧪 Testing Ramparts Docker images..."

# Test server image
echo "Testing HTTP server..."
docker run -d --name test-server -p 8080:8080 ghcr.io/shadnygren/ramparts-server:shadnygren-github-actions
sleep 5

# Test API
curl -X POST http://localhost:8080/v1/ramparts/scan \
  -H "Content-Type: application/json" \
  -d '{"url": "https://httpbin.org/json", "timeout": 30}' | jq .

docker stop test-server && docker rm test-server

# Test MCP image
echo "Testing MCP server..."
docker run --rm ghcr.io/shadnygren/ramparts-mcp:shadnygren-github-actions --version

echo "✅ Tests complete!"
EOF
chmod +x test-ramparts.sh

# Create a welcome message
cat > CODESPACE_README.md << 'EOF'
# 🎉 Welcome to Ramparts Codespace!

Your development environment is ready. Here's what's been set up:

## ✅ Pre-installed Tools
- Rust toolchain with cargo, rustfmt, and clippy
- Docker and Docker Compose
- Python 3.11 with FastMCP
- GitHub CLI
- jq and curl for testing

## 📦 Available Docker Images
- `ghcr.io/shadnygren/ramparts-server:shadnygren-github-actions` - HTTP API server
- `ghcr.io/shadnygren/ramparts-mcp:shadnygren-github-actions` - MCP stdio server

## 🚀 Quick Start Commands

### Test Docker Images
```bash
./test-ramparts.sh
```

### Run HTTP Server
```bash
docker run -p 8080:8080 ghcr.io/shadnygren/ramparts-server:shadnygren-github-actions
```

### Run MCP Server
```bash
docker run -it ghcr.io/shadnygren/ramparts-mcp:shadnygren-github-actions
```

### Build from Source
```bash
cargo build --release --all-features
```

### Run Tests
```bash
cargo test --all-features
```

## 📝 Important Notes
- This Codespace has a modern CPU (AVX2 support), so all binaries will work!
- The Docker images were built on GitHub Actions
- Port 8080 is forwarded for the HTTP server
- Check RAMPARTS_REVIEW_2025-09-22.md for project status

## 🐛 Known Issues
- MCP server mode has issues due to rmcp library problems
- Scanner functionality works well
- HTTP API server is fully functional
EOF

echo ""
echo "✅ Codespace setup complete!"
echo "📖 Check CODESPACE_README.md for quick start guide"
echo ""
docker images | grep ramparts || echo "Note: Docker images not available yet"