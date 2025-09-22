# Test Harness Directory Index

## Files Overview

### 1. **mcp_test_harness.py**
- **Purpose**: Comprehensive MCP server testing framework
- **Features**:
  - Tests MCP servers running in Docker containers
  - Supports HTTP+SSE and Streaming HTTP transports
  - Secondary support for stdio transport
  - Uses FastMCP client library
  - Generates detailed test reports with pass/fail statistics
  - Supports interactive tool testing
  - Can save reports to JSON files
- **Usage**: `python3 mcp_test_harness.py [server] --sse --verbose --save-report [file]`

### 2. **test_ramparts.py**
- **Purpose**: Main test script for Ramparts MCP server
- **Features**:
  - Tests Ramparts-specific MCP capabilities
  - Validates security scanning features
  - Tests tool enumeration and execution

### 3. **test_ramparts_mcp_stdio.py**
- **Purpose**: Tests Ramparts MCP server using stdio transport
- **Features**:
  - Tests stdio-based MCP communication
  - Validates JSON-RPC protocol over stdin/stdout
  - Tests with Docker containers using stdio

### 4. **test_ramparts_direct.py**
- **Purpose**: Direct testing of Ramparts without Docker
- **Features**:
  - Tests Ramparts binary directly
  - No Docker container overhead
  - Direct process spawning and communication

### 5. **test_mcp_client.py**
- **Purpose**: Simple MCP client implementation
- **Features**:
  - Basic MCP client for testing
  - JSON-RPC protocol implementation
  - Initialize session, list tools/resources/prompts
  - Call tools with arguments
  - Designed for stdio transport with Docker

### 6. **ramparts_self_scan.py**
- **Purpose**: Ramparts self-scanning test
- **Features**:
  - Uses Ramparts to scan another MCP server
  - Demonstrates Ramparts scanning capabilities
  - Generates security reports
  - Tests Ramparts-on-Ramparts scanning

### 7. **docker_test_report.py**
- **Purpose**: Docker-based testing and reporting
- **Features**:
  - Tests Ramparts Docker images
  - Generates comprehensive test reports
  - Validates Docker container functionality

### 8. **quick_test.py**
- **Purpose**: Quick smoke tests for Ramparts
- **Features**:
  - Fast validation of basic functionality
  - Minimal test suite for rapid feedback
  - Basic connectivity and response tests

### 9. **setup_and_test.sh**
- **Purpose**: Shell script for setup and testing
- **Features**:
  - Sets up test environment
  - Runs test suite
  - Handles dependencies and configuration

### 10. **example_servers.json**
- **Purpose**: Configuration file with example MCP servers
- **Content**: JSON configuration for various MCP server endpoints to test against

### 11. **requirements.txt**
- **Purpose**: Python dependencies for test harness
- **Content**: List of required Python packages (fastmcp, httpx, etc.)

### 12. **README.md**
- **Purpose**: Documentation for the test harness
- **Content**: Setup instructions, usage examples, and test descriptions

### 13. **ramparts_docker_test_report_20250919_000941.json**
- **Purpose**: Sample test report output
- **Content**: JSON-formatted test results from a previous test run

### 14. **ramparts_security_scan_20250919_002444.json**
- **Purpose**: Sample security scan output
- **Content**: JSON-formatted security scan results from Ramparts

### 15. **venv/**
- **Purpose**: Python virtual environment
- **Content**: Installed packages including fastmcp and dependencies

## Key Testing Capabilities

1. **MCP Protocol Testing**: Full JSON-RPC protocol validation
2. **Transport Testing**: HTTP, SSE, stdio transport support
3. **Docker Integration**: Test containers with various configurations
4. **Security Scanning**: Validate Ramparts security analysis features
5. **Report Generation**: JSON and human-readable test reports
6. **Interactive Testing**: Manual tool invocation and testing

## Usage Examples

```bash
# Test with MCP test harness
python3 mcp_test_harness.py http://localhost:8002 --sse --verbose

# Test with simple MCP client
python3 test_mcp_client.py

# Run self-scan test
python3 ramparts_self_scan.py

# Quick smoke test
python3 quick_test.py
```