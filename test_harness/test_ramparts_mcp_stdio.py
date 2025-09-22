#!/usr/bin/env python3
"""
Test Ramparts MCP Server via stdio transport using Docker
Lists all tools, prompts, and resources exposed by Ramparts
"""

import asyncio
import json
from mcp_test_harness import MCPTestHarness, TransportType, TestStatus
from typing import Dict, Any, List


async def list_ramparts_capabilities():
    """Connect to Ramparts MCP server and list all capabilities"""

    print("\n" + "="*70)
    print("🛡️  RAMPARTS MCP SERVER CAPABILITY DISCOVERY")
    print("="*70)

    # Configure Ramparts server connection via Docker
    config = {
        "name": "Ramparts Security Scanner",
        "transport": TransportType.STDIO,
        "command": ["docker", "run", "-i", "--rm", "ramparts:local"],
        "env": {},
        "cwd": None
    }

    # Create test harness
    harness = MCPTestHarness()

    try:
        print("\n🔌 Connecting to Ramparts MCP Server via Docker stdio...")
        print("-" * 60)

        # Set configuration
        harness.server_config = config

        # Initialize connection
        init_result = await harness.test_initialization()

        if init_result.status != TestStatus.PASSED:
            print(f"❌ Failed to initialize: {init_result.error or init_result.message}")
            return

        print("✅ Successfully connected to Ramparts MCP Server")

        # Get server info from details
        if init_result.details:
            server_info = init_result.details.get('server_info', {})
            if server_info:
                print(f"\n📋 Server Information:")
                print(f"   Name: {server_info.get('name', 'Unknown')}")
                print(f"   Version: {server_info.get('version', 'Unknown')}")

            capabilities = init_result.details.get('capabilities', {})
            if capabilities:
                print(f"\n   Capabilities:")
                for cap, details in capabilities.items():
                    if isinstance(details, dict) and details:
                        print(f"      • {cap}: enabled")
                    elif details:
                        print(f"      • {cap}: {details}")

        # List Tools
        print("\n" + "="*70)
        print("🔧 AVAILABLE TOOLS")
        print("="*70)

        tools_result = await harness.test_list_tools()

        if tools_result.status == TestStatus.PASSED and tools_result.details.get('tools'):
            print(f"\nFound {len(tools_result.tools)} tools:\n")

            for i, tool in enumerate(tools_result.tools, 1):
                print(f"{i}. Tool: {tool['name']}")
                if tool.get('description'):
                    # Format long descriptions
                    desc = tool['description']
                    if len(desc) > 100:
                        desc = desc[:97] + "..."
                    print(f"   Description: {desc}")

                # Show input schema if available
                if tool.get('inputSchema'):
                    schema = tool['inputSchema']
                    if isinstance(schema, dict):
                        properties = schema.get('properties', {})
                        required = schema.get('required', [])
                        if properties:
                            print(f"   Parameters:")
                            for param, details in properties.items():
                                req_marker = " (required)" if param in required else " (optional)"
                                param_type = details.get('type', 'unknown')
                                param_desc = details.get('description', '')
                                if param_desc:
                                    param_desc = f" - {param_desc[:50]}"
                                print(f"      • {param}: {param_type}{req_marker}{param_desc}")
                print()
        else:
            print("❌ No tools found or failed to list tools")
            if tools_result.error:
                print(f"   Error: {tools_result.error}")

        # List Resources
        print("\n" + "="*70)
        print("📚 AVAILABLE RESOURCES")
        print("="*70)

        resources_result = await harness.test_list_resources()

        if resources_result.status == TestStatus.PASSED and resources_result.details.get('resources'):
            resources = resources_result.details['resources']
            print(f"\nFound {len(resources)} resources:\n")

            for i, resource in enumerate(resources, 1):
                print(f"{i}. Resource: {resource.get('name', 'Unknown')}")
                if resource.get('uri'):
                    print(f"   URI: {resource['uri']}")
                if resource.get('description'):
                    desc = resource['description']
                    if len(desc) > 100:
                        desc = desc[:97] + "..."
                    print(f"   Description: {desc}")
                if resource.get('mimeType'):
                    print(f"   MIME Type: {resource['mimeType']}")
                print()
        else:
            print("\n📭 No resources exposed by this server")

        # List Prompts
        print("\n" + "="*70)
        print("💬 AVAILABLE PROMPTS")
        print("="*70)

        prompts_result = await harness.test_list_prompts()

        if prompts_result.status == TestStatus.PASSED and prompts_result.details.get('prompts'):
            prompts = prompts_result.details['prompts']
            print(f"\nFound {len(prompts)} prompts:\n")

            for i, prompt in enumerate(prompts, 1):
                print(f"{i}. Prompt: {prompt.get('name', 'Unknown')}")
                if prompt.get('description'):
                    desc = prompt['description']
                    if len(desc) > 100:
                        desc = desc[:97] + "..."
                    print(f"   Description: {desc}")

                # Show arguments if available
                if prompt.get('arguments'):
                    print(f"   Arguments:")
                    for arg in prompt['arguments']:
                        arg_name = arg.get('name', 'unknown')
                        arg_desc = arg.get('description', '')
                        arg_req = " (required)" if arg.get('required') else " (optional)"
                        if arg_desc:
                            arg_desc = f" - {arg_desc[:50]}"
                        print(f"      • {arg_name}{arg_req}{arg_desc}")
                print()
        else:
            print("\n📭 No prompts exposed by this server")

        # Summary
        print("\n" + "="*70)
        print("📊 CAPABILITY SUMMARY")
        print("="*70)

        total_capabilities = 0
        summary = []

        if tools_result.status == TestStatus.PASSED and tools_result.details.get('tools'):
            count = len(tools_result.details['tools'])
            total_capabilities += count
            summary.append(f"🔧 {count} Tools")

        if resources_result.status == TestStatus.PASSED and resources_result.details.get('resources'):
            count = len(resources_result.details['resources'])
            total_capabilities += count
            summary.append(f"📚 {count} Resources")

        if prompts_result.status == TestStatus.PASSED and prompts_result.details.get('prompts'):
            count = len(prompts_result.details['prompts'])
            total_capabilities += count
            summary.append(f"💬 {count} Prompts")

        print(f"\nTotal Capabilities: {total_capabilities}")
        if summary:
            print("Breakdown: " + " | ".join(summary))

        print("\n✅ Capability discovery completed successfully!")

    except Exception as e:
        print(f"\n❌ Error during capability discovery: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup (close client if exists)
        if hasattr(harness, 'client') and harness.client:
            await harness.client.__aexit__(None, None, None)


async def main():
    """Main entry point"""
    await list_ramparts_capabilities()


if __name__ == "__main__":
    asyncio.run(main())