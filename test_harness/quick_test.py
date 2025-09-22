#!/usr/bin/env python3
"""
Quick test to verify Ramparts Docker image functionality
"""

import asyncio
import json
import sys
import time
from datetime import datetime

# Test basic MCP stdio communication
async def test_stdio_mode():
    """Test Ramparts in default stdio mode"""
    print("Testing Ramparts MCP Server (stdio mode)")
    print("=" * 50)

    import subprocess

    try:
        # Send a basic JSON-RPC initialize request
        test_request = json.dumps({
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "1.0.0",
                "capabilities": {}
            },
            "id": 1
        })

        print(f"Sending: {test_request[:100]}...")

        # Run the container with the request
        result = subprocess.run(
            ["docker", "run", "-i", "--rm", "ramparts:local"],
            input=test_request.encode(),
            capture_output=True,
            timeout=5
        )

        print(f"Exit code: {result.returncode}")

        if result.stdout:
            print(f"Stdout: {result.stdout.decode()[:200]}")
        if result.stderr:
            print(f"Stderr: {result.stderr.decode()[:200]}")

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print("❌ Timeout - container didn't respond")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


# Test that the container at least starts
async def test_container_starts():
    """Test if container starts at all"""
    print("\nTesting container startup")
    print("=" * 50)

    import subprocess

    try:
        # Try to run with a simple command override
        result = subprocess.run(
            ["docker", "run", "--rm", "--entrypoint", "echo", "ramparts:local", "Container works!"],
            capture_output=True,
            timeout=5
        )

        output = result.stdout.decode().strip()
        print(f"Output: {output}")

        if output == "Container works!":
            print("✅ Container can execute commands")
            return True
        else:
            print("❌ Unexpected output")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


# Test using the test harness
async def test_with_harness():
    """Test using the MCP test harness"""
    print("\nTesting with MCP Test Harness")
    print("=" * 50)

    try:
        from mcp_test_harness import MCPTestHarness

        harness = MCPTestHarness(timeout=10.0, verbose=True)

        # Test stdio transport with Docker
        config = {
            "name": "Ramparts Docker (stdio)",
            "command": "docker",
            "args": ["run", "-i", "--rm", "ramparts:local"],
            "env": {}
        }

        connected = await harness.connect(config)

        if connected:
            print("✅ Connected via test harness")

            # Try to run basic tests
            report = await harness.run_comprehensive_tests()

            # Print summary
            print(f"\nTest Summary:")
            print(f"  Total: {report.total_tests}")
            print(f"  Passed: {report.passed}")
            print(f"  Failed: {report.failed}")
            print(f"  Success Rate: {report.success_rate():.1f}%")

            # Save report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = f"ramparts_quick_test_{timestamp}.json"
            harness.save_report(report_file)
            print(f"\n💾 Report saved to: {report_file}")

            await harness.disconnect()
            return report.success_rate() > 50
        else:
            print("❌ Failed to connect via test harness")
            return False

    except ImportError:
        print("❌ Test harness not found")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n🚀 RAMPARTS DOCKER IMAGE QUICK TEST")
    print("="*60)

    results = []

    # Test 1: Container starts
    print("\n[Test 1] Container Startup")
    result = await test_container_starts()
    results.append(("Container Startup", result))

    # Test 2: stdio mode
    print("\n[Test 2] stdio Mode")
    result = await test_stdio_mode()
    results.append(("stdio Mode", result))

    # Test 3: MCP Test Harness
    print("\n[Test 3] MCP Test Harness")
    result = await test_with_harness()
    results.append(("MCP Test Harness", result))

    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)

    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {test_name}: {status}")

    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)

    print(f"\nTotal: {total_passed}/{total_tests} passed")

    if total_passed == total_tests:
        print("🎉 All tests passed!")
        return 0
    elif total_passed > 0:
        print("⚠️ Some tests failed")
        return 1
    else:
        print("❌ All tests failed")
        return 2


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)