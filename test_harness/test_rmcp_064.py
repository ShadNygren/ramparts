#!/usr/bin/env python3
"""
Test script to verify that tools are exposed after upgrading to rmcp 0.6.4
"""

import json
import subprocess
import sys

def test_mcp_tools(image_name="ramparts:v2025-09-21t16-45-rmcp-064"):
    """Test if MCP server properly exposes tools with rmcp 0.6.4"""

    print(f"Testing image: {image_name}")
    print("Testing with rmcp v0.6.4 (official modelcontextprotocol/rust-sdk)")
    print("=" * 60)

    # Prepare MCP protocol messages
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

    initialized_notif = {
        "jsonrpc": "2.0",
        "method": "initialized",
        "params": {}
    }

    list_tools_req = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "params": {},
        "id": 2
    }

    # Send all requests
    requests = "\n".join([
        json.dumps(init_req),
        json.dumps(initialized_notif),
        json.dumps(list_tools_req)
    ])

    # Run Docker container
    try:
        result = subprocess.run(
            ["docker", "run", "-i", "--rm", image_name],
            input=requests.encode(),
            capture_output=True,
            text=False,
            timeout=10
        )
    except subprocess.TimeoutExpired:
        print("❌ Docker container timed out")
        return False
    except Exception as e:
        print(f"❌ Error running Docker: {e}")
        return False

    # Parse responses
    output = result.stdout.decode('utf-8', errors='ignore')
    stderr = result.stderr.decode('utf-8', errors='ignore')

    if stderr:
        print("STDERR:")
        print(stderr)

    # Check for tools in responses
    tools_found = False
    tool_count = 0
    tool_names = []

    for line in output.split('\n'):
        if line.strip():
            try:
                data = json.loads(line)

                # Check initialize response
                if data.get('id') == 1 and 'result' in data:
                    capabilities = data['result'].get('capabilities', {})
                    if 'tools' in capabilities:
                        print(f"✅ Tools capability enabled in initialize response")
                    else:
                        print(f"❌ No tools capability in initialize response")

                # Check tools/list response
                if data.get('id') == 2 and 'result' in data:
                    tools = data['result'].get('tools', [])
                    tool_count = len(tools)
                    if tools:
                        tools_found = True
                        print(f"\n✅ Found {tool_count} tools:")
                        for tool in tools:
                            name = tool.get('name', 'unknown')
                            desc = tool.get('description', '')
                            tool_names.append(name)
                            print(f"  - {name}: {desc}")
                    else:
                        print("\n❌ Empty tools array in tools/list response")

            except json.JSONDecodeError:
                # Non-JSON output, ignore
                pass

    # Final verdict
    print("\n" + "=" * 60)
    if tools_found and tool_count > 0:
        print(f"🎉 SUCCESS! MCP server exposes {tool_count} tools: {', '.join(tool_names)}")
        print("The upgrade to rmcp 0.6.4 fixed the issue!")
        print("\n** CRITICAL DISCOVERY CONFIRMED **")
        print("The issue was using an outdated rmcp version (0.3.2).")
        print("Upgrading to the official modelcontextprotocol/rust-sdk v0.6.4 resolved it!")
        return True
    else:
        print("❌ FAILED: Tools are still not exposed")
        print("Even with rmcp 0.6.4, the tools are not being registered")
        print("Further investigation required...")
        return False

if __name__ == "__main__":
    image = sys.argv[1] if len(sys.argv) > 1 else "ramparts:v2025-09-21t16-45-rmcp-064"
    success = test_mcp_tools(image)
    sys.exit(0 if success else 1)