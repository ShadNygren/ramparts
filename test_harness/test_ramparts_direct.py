#!/usr/bin/env python3
"""
Direct test of Ramparts MCP server using proper JSON-RPC protocol
"""

import json
import subprocess
import sys


def send_mcp_request(request):
    """Send MCP request to Ramparts Docker container"""
    request_json = json.dumps(request) + "\n"

    try:
        result = subprocess.run(
            ["docker", "run", "-i", "--rm", "ramparts:local"],
            input=request_json.encode(),
            capture_output=True,
            timeout=5
        )

        if result.stdout:
            # Parse each line as potential JSON-RPC response
            lines = result.stdout.decode().strip().split('\n')
            for line in lines:
                if line.strip():
                    try:
                        return json.loads(line)
                    except json.JSONDecodeError:
                        continue

        if result.stderr:
            print(f"STDERR: {result.stderr.decode()}", file=sys.stderr)

        return None

    except subprocess.TimeoutExpired:
        print("Request timed out", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return None


def main():
    print("="*70)
    print("RAMPARTS MCP SERVER DIRECT TEST")
    print("="*70)

    # Test 1: Initialize
    print("\n1. Testing Initialize...")
    init_request = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "1.0.0",
            "capabilities": {},
            "clientInfo": {
                "name": "RampartsDirectTest",
                "version": "1.0.0"
            }
        },
        "id": 1
    }

    response = send_mcp_request(init_request)
    if response:
        print(f"✅ Initialize response received:")
        print(json.dumps(response, indent=2))
    else:
        print("❌ No response to initialize")
        return 1

    # Test 2: List Tools
    print("\n2. Testing List Tools...")
    tools_request = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "params": {},
        "id": 2
    }

    response = send_mcp_request(tools_request)
    if response:
        print(f"✅ Tools list response received:")
        print(json.dumps(response, indent=2))

        if "result" in response and "tools" in response["result"]:
            tools = response["result"]["tools"]
            print(f"\nFound {len(tools)} tools:")
            for tool in tools:
                print(f"  • {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')}")
    else:
        print("❌ No response to tools/list")

    # Test 3: Call Health Tool
    print("\n3. Testing Health Tool...")
    health_request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "health",
            "arguments": {}
        },
        "id": 3
    }

    response = send_mcp_request(health_request)
    if response:
        print(f"✅ Health tool response received:")
        print(json.dumps(response, indent=2))
    else:
        print("❌ No response to health tool")

    # Test 4: Test Scan Tool (scan a test MCP server)
    print("\n4. Testing Scan Tool...")
    scan_request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "scan",
            "arguments": {
                "url": "http://example.com/mcp",
                "detailed": True,
                "format": "json"
            }
        },
        "id": 4
    }

    response = send_mcp_request(scan_request)
    if response:
        print(f"✅ Scan tool response received:")
        print(json.dumps(response, indent=2))
    else:
        print("❌ No response to scan tool")

    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)

    return 0


if __name__ == "__main__":
    sys.exit(main())