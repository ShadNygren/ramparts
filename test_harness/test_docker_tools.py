#!/usr/bin/env python3

import json
import subprocess
import sys

def test_mcp_server(image_name):
    """Test MCP server tools listing"""

    # Initialize request
    init_req = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"experimental": {}, "sampling": {}},
            "clientInfo": {"name": "test-client", "version": "1.0"}
        },
        "id": 1
    }

    # Initialized notification
    initialized_notif = {
        "jsonrpc": "2.0",
        "method": "initialized",
        "params": {}
    }

    # List tools request
    list_tools_req = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "params": {},
        "id": 2
    }

    # Combine all requests
    requests = "\n".join([
        json.dumps(init_req),
        json.dumps(initialized_notif),
        json.dumps(list_tools_req)
    ])

    print(f"Testing image: {image_name}")
    print("=" * 60)

    # Run docker container
    result = subprocess.run(
        ["docker", "run", "-i", "--rm", image_name],
        input=requests.encode(),
        capture_output=True,
        text=False
    )

    # Parse responses
    output = result.stdout.decode('utf-8', errors='ignore')
    stderr = result.stderr.decode('utf-8', errors='ignore')

    print("STDOUT:")
    for line in output.split('\n'):
        if line.strip():
            try:
                data = json.loads(line)
                if 'id' in data:
                    print(f"Response {data['id']}: {json.dumps(data, indent=2)}")
            except:
                print(f"Non-JSON: {line}")

    if stderr:
        print("\nSTDERR:")
        print(stderr)

    # Try to find tools in response
    for line in output.split('\n'):
        if '"id":2' in line:
            try:
                response = json.loads(line)
                if 'result' in response and 'tools' in response['result']:
                    tools = response['result']['tools']
                    print(f"\n✅ Found {len(tools)} tools:")
                    for tool in tools:
                        print(f"  - {tool.get('name', 'unknown')}: {tool.get('description', '')}")
                    return True
            except:
                pass

    print("\n❌ No tools found in response")
    return False

if __name__ == "__main__":
    image = sys.argv[1] if len(sys.argv) > 1 else "ramparts:v2025-09-21t12-30"
    test_mcp_server(image)