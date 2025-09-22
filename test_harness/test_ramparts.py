#!/usr/bin/env python3
"""
Test script specifically for testing the Ramparts MCP server Docker image
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path to import test harness
sys.path.insert(0, str(Path(__file__).parent))

from mcp_test_harness import MCPTestHarness, DockerMCPTester, ServerTestReport


async def test_ramparts_stdio_mode():
    """Test Ramparts in stdio mode (default Docker mode)"""
    print("\n" + "="*60)
    print("TESTING RAMPARTS IN STDIO MODE (Docker Default)")
    print("="*60)

    harness = MCPTestHarness(verbose=True, timeout=10.0)

    # Test stdio mode by running the container directly
    config = {
        "name": "Ramparts MCP Server (stdio)",
        "command": "docker",
        "args": ["run", "-i", "--rm", "ramparts:local"],
        "env": {}
    }

    try:
        connected = await harness.connect(config)
        if connected:
            report = await harness.run_comprehensive_tests()
            harness.print_report()
            return report
        else:
            print("❌ Failed to connect to Ramparts in stdio mode")
            return None
    finally:
        await harness.disconnect()


async def test_ramparts_http_mode():
    """Test Ramparts in HTTP server mode"""
    print("\n" + "="*60)
    print("TESTING RAMPARTS IN HTTP SERVER MODE")
    print("="*60)

    # Use DockerMCPTester for HTTP mode testing
    tester = DockerMCPTester(
        container_name="ramparts-test-http",
        port=8080,
        use_sse=False  # Ramparts uses standard HTTP, not SSE
    )

    # Test with the local ramparts image
    report = await tester.test_docker_mcp_server(
        image="ramparts:local",
        start_fresh=True,
        cleanup=True
    )

    return report


async def test_ramparts_scan_capabilities():
    """Test Ramparts scanning capabilities with sample tool calls"""
    print("\n" + "="*60)
    print("TESTING RAMPARTS SCANNING CAPABILITIES")
    print("="*60)

    harness = MCPTestHarness(verbose=True, timeout=30.0)

    # Connect to running Ramparts HTTP server
    url = "http://localhost:8080"

    try:
        # First, start the container
        print("🐳 Starting Ramparts container for scanning tests...")
        tester = DockerMCPTester("ramparts-scan-test", 8080)
        tester.stop_container()  # Clean up any existing

        success = tester.start_container(
            "ramparts:local",
            ["--entrypoint", "/app/ramparts", "ramparts:local", "server", "--port", "8080", "--host", "0.0.0.0"]
        )

        if not success:
            print("❌ Failed to start container")
            return None

        # Wait for startup
        await asyncio.sleep(3)

        connected = await harness.connect(url)
        if not connected:
            print("❌ Failed to connect")
            return None

        # Get available tools
        print("\n🔧 Testing Ramparts scanning tools...")
        tools = await harness.client.list_tools()

        # Test scan tool if available
        scan_tool = next((t for t in tools if 'scan' in t.name.lower()), None)
        if scan_tool:
            print(f"\n📡 Testing tool: {scan_tool.name}")

            # Test scanning a known MCP server
            test_args = {
                "url": "http://example.com/mcp",  # Example URL
                "timeout": 5
            }

            result = await harness.test_tool_execution(scan_tool.name, test_args)
            harness.report.add_result(result)
            print(f"   Result: {result.status.value}")

        # Test scan-config tool if available
        config_tool = next((t for t in tools if 'config' in t.name.lower()), None)
        if config_tool:
            print(f"\n🔍 Testing tool: {config_tool.name}")

            result = await harness.test_tool_execution(config_tool.name, {})
            harness.report.add_result(result)
            print(f"   Result: {result.status.value}")

        harness.print_report()
        return harness.report

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return None
    finally:
        await harness.disconnect()
        # Cleanup
        tester.stop_container()


async def test_ramparts_comprehensive():
    """Run comprehensive tests on Ramparts MCP server"""
    print("\n" + "="*80)
    print("🚀 COMPREHENSIVE RAMPARTS MCP SERVER TESTING")
    print("="*80)

    all_reports = []

    # Test 1: HTTP Server Mode
    print("\n[TEST 1] HTTP Server Mode")
    report = await test_ramparts_http_mode()
    if report:
        all_reports.append(report)

    # Test 2: Scanning Capabilities (if HTTP server is available)
    print("\n[TEST 2] Scanning Capabilities")
    report = await test_ramparts_scan_capabilities()
    if report:
        all_reports.append(report)

    # Note: stdio mode testing requires different approach
    # as it needs bidirectional communication through stdin/stdout
    # which is complex with Docker

    # Generate summary
    print("\n" + "="*80)
    print("📊 OVERALL TEST SUMMARY")
    print("="*80)

    total_tests = sum(r.total_tests for r in all_reports)
    total_passed = sum(r.passed for r in all_reports)
    total_failed = sum(r.failed for r in all_reports)
    total_errors = sum(r.errors for r in all_reports)

    print(f"\nTotal Test Suites: {len(all_reports)}")
    print(f"Total Tests Run: {total_tests}")
    print(f"✅ Total Passed: {total_passed}")
    print(f"❌ Total Failed: {total_failed}")
    print(f"🔥 Total Errors: {total_errors}")

    if total_tests > 0:
        success_rate = (total_passed / total_tests) * 100
        print(f"📈 Overall Success Rate: {success_rate:.1f}%")

        if success_rate >= 90:
            print("\n🎉 EXCELLENT: Ramparts MCP server is working great!")
        elif success_rate >= 70:
            print("\n✅ GOOD: Ramparts MCP server is mostly functional")
        elif success_rate >= 50:
            print("\n⚠️ FAIR: Ramparts MCP server has some issues")
        else:
            print("\n❌ POOR: Ramparts MCP server has significant issues")

    # Save comprehensive report
    timestamp = asyncio.get_event_loop().time()
    report_file = f"ramparts_test_report_{int(timestamp)}.json"

    comprehensive_report = {
        "test_suite": "Ramparts MCP Server Comprehensive Test",
        "timestamp": str(timestamp),
        "summary": {
            "total_test_suites": len(all_reports),
            "total_tests": total_tests,
            "passed": total_passed,
            "failed": total_failed,
            "errors": total_errors,
            "success_rate": (total_passed / total_tests * 100) if total_tests > 0 else 0
        },
        "reports": [
            {
                "server_name": r.server_name,
                "transport": r.transport_type.value,
                "tests": r.total_tests,
                "passed": r.passed,
                "failed": r.failed,
                "success_rate": r.success_rate()
            } for r in all_reports
        ]
    }

    with open(report_file, 'w') as f:
        json.dump(comprehensive_report, f, indent=2)

    print(f"\n💾 Comprehensive report saved to: {report_file}")


async def main():
    """Main test runner"""
    import argparse

    parser = argparse.ArgumentParser(description="Test Ramparts MCP Server")
    parser.add_argument("--mode", choices=["http", "stdio", "scan", "all"], default="all",
                       help="Test mode to run")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if args.mode == "http":
        await test_ramparts_http_mode()
    elif args.mode == "stdio":
        await test_ramparts_stdio_mode()
    elif args.mode == "scan":
        await test_ramparts_scan_capabilities()
    else:
        await test_ramparts_comprehensive()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        sys.exit(1)