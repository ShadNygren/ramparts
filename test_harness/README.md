# MCP Server Test Harness

A comprehensive testing framework for Model Context Protocol (MCP) servers, with special focus on Docker-based deployments and HTTP transports.

## Features

- **Multi-Transport Support**: HTTP, SSE (Server-Sent Events), and stdio
- **Docker Integration**: Specialized testing for MCP servers running in Docker containers
- **Comprehensive Testing**: Connection, initialization, tool listing, resource discovery, performance testing
- **Interactive Mode**: Manual tool testing with custom arguments
- **Detailed Reporting**: JSON reports with performance metrics and success rates
- **Batch Testing**: Test multiple servers from configuration files

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### Test the Ramparts Docker Image

```bash
# Run comprehensive Ramparts tests
python test_ramparts.py

# Test specific mode
python test_ramparts.py --mode http    # HTTP server mode
python test_ramparts.py --mode scan    # Scanning capabilities
python test_ramparts.py --mode all     # All tests
```

### Test Any MCP Server

```bash
# Test HTTP-based MCP server
python mcp_test_harness.py http://localhost:8080

# Test SSE-based MCP server
python mcp_test_harness.py http://localhost:8080/sse --sse

# Test stdio-based MCP server
python mcp_test_harness.py "npx mcp-server-example"

# Test Docker container
python mcp_test_harness.py --docker --image ramparts:local --port 8080
```

## Usage Examples

### 1. Basic Server Testing

```python
import asyncio
from mcp_test_harness import MCPTestHarness

async def test_server():
    harness = MCPTestHarness(verbose=True)

    # Connect to server
    connected = await harness.connect("http://localhost:8080")

    if connected:
        # Run comprehensive tests
        report = await harness.run_comprehensive_tests()

        # Print results
        harness.print_report()

        # Save report to file
        harness.save_report("test_report.json")

    await harness.disconnect()

asyncio.run(test_server())
```

### 2. Docker Container Testing

```python
from mcp_test_harness import DockerMCPTester

async def test_docker():
    tester = DockerMCPTester(
        container_name="my-mcp-server",
        port=8080,
        use_sse=False
    )

    report = await tester.test_docker_mcp_server(
        image="my-mcp-image:latest",
        start_fresh=True,  # Start new container
        cleanup=True        # Clean up after testing
    )

    if report:
        print(f"Success rate: {report.success_rate():.1f}%")
```

### 3. Batch Testing Multiple Servers

Create a configuration file `servers.json`:

```json
{
  "mcpServers": {
    "server1": {
      "name": "Production MCP Server",
      "url": "https://api.example.com/mcp"
    },
    "server2": {
      "name": "Development MCP Server",
      "url": "http://localhost:8080"
    },
    "server3": {
      "name": "Local stdio server",
      "command": "npx",
      "args": ["mcp-server-filesystem"],
      "env": {}
    }
  }
}
```

Then test all servers:

```bash
python mcp_test_harness.py --config servers.json --save-report batch_report.json
```

## Test Harness Architecture

### Core Components

1. **MCPTestHarness**: Main testing class
   - Handles connections to MCP servers
   - Runs comprehensive test suites
   - Generates detailed reports

2. **DockerMCPTester**: Docker-specific testing
   - Manages Docker container lifecycle
   - Tests containerized MCP servers
   - Handles port mapping and cleanup

3. **TestResult**: Individual test results
   - Tracks status, duration, and details
   - Supports multiple status types (PASSED, FAILED, TIMEOUT, ERROR)

4. **ServerTestReport**: Complete test reports
   - Aggregates all test results
   - Calculates success rates
   - Provides JSON serialization

### Test Coverage

The harness runs the following tests:

1. **Connection Test**: Verifies server connectivity
2. **Initialization Test**: Tests MCP protocol initialization
3. **Tool Discovery**: Lists and validates available tools
4. **Resource Discovery**: Lists available resources
5. **Prompt Discovery**: Lists available prompts
6. **Performance Test**: Measures response times with multiple requests
7. **Tool Execution**: Tests specific tool calls (interactive mode)

## Command Line Options

```bash
mcp_test_harness.py [options]

Options:
  server              Server URL or command to test
  --docker           Test Docker container
  --image IMAGE      Docker image to test (default: ramparts:local)
  --port PORT        Port for Docker container (default: 8080)
  --sse              Use SSE transport
  --config FILE      Path to MCP config file
  --verbose          Enable verbose output
  --interactive      Enable interactive tool testing
  --save-report FILE Save test report to file
  --timeout SECONDS  Request timeout (default: 30)
```

## Test Reports

Reports include:

- **Summary Statistics**: Total tests, pass/fail counts, success rate
- **Performance Metrics**: Response times (min/avg/max)
- **Tool Inventory**: Available tools, resources, and prompts
- **Error Details**: Detailed error messages and stack traces
- **Timing Information**: Duration of each test

Example report structure:

```json
{
  "server_name": "Ramparts MCP Server",
  "server_url": "http://localhost:8080",
  "transport_type": "http",
  "total_tests": 5,
  "passed": 4,
  "failed": 1,
  "success_rate": 80.0,
  "test_results": [
    {
      "test_name": "Connection",
      "status": "PASSED",
      "duration_ms": 125.4,
      "message": "Connected successfully"
    }
  ]
}
```

## Testing Ramparts Specifically

The `test_ramparts.py` script provides specialized testing for the Ramparts MCP security scanner:

```bash
# Full comprehensive test
python test_ramparts.py

# Test HTTP server mode only
python test_ramparts.py --mode http

# Test scanning capabilities
python test_ramparts.py --mode scan
```

This will:
1. Start Ramparts in a Docker container
2. Test HTTP server mode functionality
3. Test scanning capabilities
4. Generate a comprehensive report
5. Clean up containers after testing

## Troubleshooting

### Common Issues

1. **Connection Refused**: Ensure the MCP server is running and accessible
2. **Timeout Errors**: Increase timeout with `--timeout 60`
3. **Docker Permission Denied**: Ensure Docker daemon is running and user has permissions
4. **Module Not Found**: Install dependencies with `pip install -r requirements.txt`

### Debug Mode

Enable verbose logging for troubleshooting:

```bash
python mcp_test_harness.py http://localhost:8080 --verbose
```

## Development

### Extending the Test Harness

Add custom tests by extending the `MCPTestHarness` class:

```python
class CustomMCPTester(MCPTestHarness):
    async def test_custom_functionality(self):
        """Custom test implementation"""
        # Your test logic here
        return TestResult(
            test_name="Custom Test",
            status=TestStatus.PASSED,
            duration_ms=100,
            message="Custom test passed"
        )
```

### Contributing

Feel free to submit issues and enhancement requests!

## License

This test harness is provided as-is for testing MCP servers.