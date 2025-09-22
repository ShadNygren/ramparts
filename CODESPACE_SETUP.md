# GitHub Codespaces Setup for Ramparts Testing

This guide explains how to launch and use GitHub Codespaces to test Ramparts Docker images on hardware with modern CPU support (AVX2).

## 🚀 Launching a Codespace

### Option 1: From GitHub Web Interface
1. Navigate to https://github.com/ShadNygren/ramparts
2. Click the green "Code" button
3. Select the "Codespaces" tab
4. Click "Create codespace on shadnygren/github-actions"

### Option 2: From GitHub CLI
```bash
gh codespace create --repo ShadNygren/ramparts --branch shadnygren/github-actions
```

### Option 3: Direct Link
Click here to create a Codespace:
https://github.com/codespaces/new?hide_repo_select=true&ref=shadnygren/github-actions&repo=ShadNygren/ramparts

## 📋 What Gets Set Up Automatically

When the Codespace launches, the `.devcontainer/post-create.sh` script will:
1. Install Rust toolchain and development tools
2. Install Docker-in-Docker for container testing
3. Install Python with FastMCP for MCP protocol testing
4. Pull the pre-built Docker images from GHCR
5. Create test scripts for easy validation

## 🧪 Testing the Docker Images

Once the Codespace is ready (takes ~2-3 minutes), you can test:

### Quick Test Script
```bash
./test-ramparts.sh
```

### Manual Testing

#### Test HTTP Server (Deploy-Dockerfile)
```bash
# Start the server
docker run -d --name ramparts-server -p 8080:8080 ghcr.io/shadnygren/ramparts-server:shadnygren-github-actions

# Test scanning endpoint
curl -X POST http://localhost:8080/v1/ramparts/scan \
  -H "Content-Type: application/json" \
  -d '{"url": "https://httpbin.org/json", "timeout": 30}'

# Check logs
docker logs ramparts-server

# Stop server
docker stop ramparts-server && docker rm ramparts-server
```

#### Test MCP Server (MCP-Dockerfile.test)
```bash
# Test version
docker run --rm ghcr.io/shadnygren/ramparts-mcp:shadnygren-github-actions --version

# Test help
docker run --rm --entrypoint /app/ramparts ghcr.io/shadnygren/ramparts-mcp:shadnygren-github-actions --help

# Test scanning via CLI
docker run --rm --entrypoint /app/ramparts ghcr.io/shadnygren/ramparts-mcp:shadnygren-github-actions \
  scan https://httpbin.org/json --format json

# Test MCP stdio mode (will wait for input)
echo '{"jsonrpc": "2.0", "method": "initialize", "params": {"protocolVersion": "1.0", "capabilities": {}}, "id": 1}' | \
  docker run -i ghcr.io/shadnygren/ramparts-mcp:shadnygren-github-actions
```

### Test with Python FastMCP Client
```python
# test_mcp.py
import asyncio
from fastmcp import FastMCP

async def test_mcp_server():
    # This would connect to the MCP server
    # Note: Implementation depends on FastMCP API
    pass

asyncio.run(test_mcp_server())
```

## 📊 Expected Test Results

### ✅ What Should Work
- Docker images start without SIGILL errors (modern CPU in Codespace)
- HTTP server responds on port 8080
- Scanner can analyze https://httpbin.org/json
- CLI commands (--version, --help) execute successfully
- Basic scanning functionality returns results

### ⚠️ Known Issues
- MCP stdio mode may not respond due to rmcp library issues
- Some LLM features require API keys to be configured
- Complex MCP protocol operations may fail

## 🛠️ Troubleshooting

### Docker Images Not Found
If images aren't available, pull manually:
```bash
docker pull ghcr.io/shadnygren/ramparts-server:shadnygren-github-actions
docker pull ghcr.io/shadnygren/ramparts-mcp:shadnygren-github-actions
```

### Permission Issues
The Codespace runs as non-root user `vscode`. If you encounter permission issues:
```bash
sudo docker ps  # Use sudo for Docker commands if needed
```

### Port Forwarding
Ports 8080, 8081, and 3000 are automatically forwarded. Check the "Ports" tab in VS Code.

## 💰 Codespace Limits

### Free Tier (Individual)
- 60 hours/month of core hours (4-core machine = 15 actual hours)
- 15 GB storage/month
- Codespaces stop after 30 minutes of inactivity

### Best Practices to Save Hours
1. Use 2-core machine unless you need more power
2. Stop Codespace when not in use: `gh codespace stop`
3. Delete unused Codespaces: `gh codespace delete`

## 🔄 Updating the Codespace

To get latest changes:
```bash
git pull origin shadnygren/github-actions
docker pull ghcr.io/shadnygren/ramparts-server:shadnygren-github-actions
docker pull ghcr.io/shadnygren/ramparts-mcp:shadnygren-github-actions
```

## 📝 Notes

- Codespaces have modern CPUs with AVX2 support - no Ivy Bridge limitations!
- All Docker operations work natively
- Changes in Codespace can be committed back to the repository
- Codespace configuration is stored in `.devcontainer/`

## 🚀 Next Steps

1. Launch a Codespace
2. Wait for setup to complete (~2-3 minutes)
3. Run `./test-ramparts.sh` to verify everything works
4. Check `CODESPACE_README.md` in the Codespace for more commands