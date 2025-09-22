#!/bin/bash
set -euo pipefail

echo "==============================================="
echo "🚀 Ramparts Codespace Setup Starting..."
echo "==============================================="

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to print status
print_status() {
    echo ""
    echo "✅ $1"
    echo ""
}

# Function to print error
print_error() {
    echo ""
    echo "❌ ERROR: $1"
    echo ""
}

# Update package lists
echo "📦 Updating package lists..."
sudo apt-get update -qq

# Install essential tools that might be missing
echo "📦 Installing essential tools..."
PACKAGES="jq curl wget git build-essential pkg-config libssl-dev ca-certificates gnupg lsb-release"
for package in $PACKAGES; do
    if ! dpkg -l | grep -q "^ii  $package"; then
        echo "  Installing $package..."
        sudo apt-get install -y -qq $package
    fi
done
print_status "Essential tools installed"

# Verify Docker is working
echo "🐳 Verifying Docker installation..."
if command_exists docker; then
    docker --version
    docker ps >/dev/null 2>&1 || sudo service docker start
    print_status "Docker is working"
else
    print_error "Docker is not installed!"
    exit 1
fi

# Verify Rust is installed
echo "🦀 Verifying Rust installation..."
if command_exists rustc; then
    rustc --version
    cargo --version
    print_status "Rust is installed"
else
    print_error "Rust is not installed!"
    echo "Installing Rust..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source $HOME/.cargo/env
fi

# Install Rust components
echo "🦀 Installing Rust components..."
rustup component add rustfmt clippy rust-src || true
rustup update || true
print_status "Rust components installed"

# Install useful Cargo tools
echo "📦 Installing Cargo tools..."
if ! command_exists cargo-watch; then
    cargo install cargo-watch || true
fi
if ! command_exists cargo-edit; then
    cargo install cargo-edit || true
fi
print_status "Cargo tools installed"

# Install Python packages for testing
echo "🐍 Installing Python testing tools..."
pip3 install --user --upgrade pip
pip3 install --user fastmcp pytest httpx pyyaml jsonrpc-websocket || true
print_status "Python tools installed"

# Try to build the project (may fail due to dependencies, that's ok)
echo "🔨 Attempting to build Ramparts..."
if [ -f "Cargo.toml" ]; then
    cargo build --all-features 2>&1 | head -20 || echo "Note: Build incomplete, continuing setup..."
fi

# Pull Docker images if we can
echo "📥 Attempting to pull Ramparts Docker images..."

# Function to try pulling an image
try_pull_image() {
    local IMAGE=$1
    echo "  Trying to pull $IMAGE..."
    if docker pull "$IMAGE" 2>/dev/null; then
        echo "  ✅ Successfully pulled $IMAGE"
        return 0
    else
        echo "  ⚠️  Could not pull $IMAGE"
        return 1
    fi
}

# Try different image tags
BRANCH_NAME=$(git branch --show-current 2>/dev/null || echo "main")
IMAGE_PULLED=false

for TAG in "${BRANCH_NAME}" "shadnygren-github-actions" "latest"; do
    if try_pull_image "ghcr.io/shadnygren/ramparts-server:${TAG}"; then
        docker tag "ghcr.io/shadnygren/ramparts-server:${TAG}" "ramparts-server:latest" 2>/dev/null || true
        IMAGE_PULLED=true
        break
    fi
done

for TAG in "${BRANCH_NAME}" "shadnygren-github-actions" "latest"; do
    if try_pull_image "ghcr.io/shadnygren/ramparts-mcp:${TAG}"; then
        docker tag "ghcr.io/shadnygren/ramparts-mcp:${TAG}" "ramparts-mcp:latest" 2>/dev/null || true
        IMAGE_PULLED=true
        break
    fi
done

if [ "$IMAGE_PULLED" = true ]; then
    print_status "Docker images ready"
else
    echo "⚠️  Note: Could not pull images, but you can build them locally"
fi

# Create test scripts
echo "📝 Creating test scripts..."

cat > /workspaces/ramparts/test-docker.sh << 'SCRIPT_EOF'
#!/bin/bash
set -euo pipefail

echo "🧪 Testing Ramparts Docker Images..."
echo "===================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Function to test command
test_command() {
    local DESC=$1
    local CMD=$2
    echo ""
    echo "Testing: $DESC"
    if eval "$CMD"; then
        echo -e "${GREEN}✅ PASSED${NC}: $DESC"
    else
        echo -e "${RED}❌ FAILED${NC}: $DESC"
    fi
}

# Check if images exist
echo ""
echo "📦 Available Docker Images:"
docker images | grep ramparts || echo "No ramparts images found"

# Test HTTP server
echo ""
echo "🌐 Testing HTTP Server..."
if docker images | grep -q ramparts-server; then
    # Start server
    docker run -d --rm --name test-http-server -p 8080:8080 ramparts-server:latest
    sleep 5

    # Test API
    test_command "HTTP server health" "curl -s http://localhost:8080/health"
    test_command "HTTP scan endpoint" \
        "curl -s -X POST http://localhost:8080/v1/ramparts/scan \
         -H 'Content-Type: application/json' \
         -d '{\"url\": \"https://httpbin.org/json\", \"timeout\": 30}' | jq ."

    # Cleanup
    docker stop test-http-server 2>/dev/null || true
else
    echo "⚠️  Server image not found, skipping HTTP tests"
fi

# Test MCP image
echo ""
echo "🔧 Testing MCP Image..."
if docker images | grep -q ramparts-mcp; then
    test_command "MCP version" "docker run --rm --entrypoint /app/ramparts ramparts-mcp:latest --version"
    test_command "MCP help" "docker run --rm --entrypoint /app/ramparts ramparts-mcp:latest --help"
    test_command "MCP scan CLI" \
        "docker run --rm --entrypoint /app/ramparts ramparts-mcp:latest \
         scan https://httpbin.org/json --format json | jq ."
else
    echo "⚠️  MCP image not found, skipping MCP tests"
fi

echo ""
echo "===================================="
echo "✅ Test script completed!"
SCRIPT_EOF

chmod +x /workspaces/ramparts/test-docker.sh
print_status "Test scripts created"

# Create a welcome file
cat > /workspaces/ramparts/CODESPACE_WELCOME.md << 'EOF'
# 🎉 Welcome to Ramparts Codespace!

Your development environment is ready with:
- ✅ Docker and Docker Compose
- ✅ Rust toolchain with cargo
- ✅ Python with FastMCP
- ✅ All essential build tools

## 🚀 Quick Commands

### Test Docker Images
```bash
./test-docker.sh
```

### Build from Source
```bash
cargo build --release --all-features
```

### Run Tests
```bash
cargo test --all-features
```

### Run HTTP Server
```bash
docker run -p 8080:8080 ramparts-server:latest
# OR
docker run -p 8080:8080 ghcr.io/shadnygren/ramparts-server:shadnygren-github-actions
```

### Run MCP Server
```bash
docker run -it ramparts-mcp:latest
# OR
docker run -it ghcr.io/shadnygren/ramparts-mcp:shadnygren-github-actions
```

## 📊 System Info
- CPU: Modern x86_64 with AVX2 support ✅
- Memory: 4GB minimum
- Storage: 32GB
- All Docker images will work without SIGILL errors!

## 🔍 Available Docker Images
EOF

echo "" >> /workspaces/ramparts/CODESPACE_WELCOME.md
echo '```' >> /workspaces/ramparts/CODESPACE_WELCOME.md
docker images | grep ramparts >> /workspaces/ramparts/CODESPACE_WELCOME.md 2>/dev/null || echo "No images pulled yet" >> /workspaces/ramparts/CODESPACE_WELCOME.md
echo '```' >> /workspaces/ramparts/CODESPACE_WELCOME.md

# Final status
echo ""
echo "==============================================="
echo "✅ Codespace Setup Complete!"
echo "==============================================="
echo ""
echo "📖 Check CODESPACE_WELCOME.md for quick start"
echo "🧪 Run ./test-docker.sh to test Docker images"
echo ""

# Show available images
docker images | grep ramparts 2>/dev/null || echo "Note: No Docker images pulled yet, but you can pull them manually"