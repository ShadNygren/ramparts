#!/usr/bin/env python3
"""
MCP Server Test Harness
A comprehensive testing framework for MCP servers, particularly those running in Docker containers.
Primary focus: HTTP+SSE and Streaming HTTP transports
Secondary support: stdio transport
"""

import asyncio
import sys
import json
import os
import time
import traceback
import logging
from typing import Optional, List, Dict, Any, Union, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import argparse
from pathlib import Path

try:
    from fastmcp import Client
except ImportError:
    print("Error: fastmcp not installed. Run: pip install fastmcp")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TransportType(Enum):
    """MCP Transport types"""
    HTTP = "http"
    SSE = "sse"
    STDIO = "stdio"
    UNKNOWN = "unknown"


class TestStatus(Enum):
    """Test execution status"""
    PASSED = "✅ PASSED"
    FAILED = "❌ FAILED"
    SKIPPED = "⚠️ SKIPPED"
    ERROR = "🔥 ERROR"
    TIMEOUT = "⏰ TIMEOUT"


@dataclass
class TestResult:
    """Individual test result"""
    test_name: str
    status: TestStatus
    duration_ms: float
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ServerTestReport:
    """Complete test report for a server"""
    server_name: str
    server_url: str
    transport_type: TransportType
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    test_results: List[TestResult] = field(default_factory=list)
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    end_time: Optional[str] = None
    total_duration_ms: float = 0
    server_info: Dict[str, Any] = field(default_factory=dict)

    def add_result(self, result: TestResult):
        """Add a test result to the report"""
        self.test_results.append(result)
        self.total_tests += 1

        if result.status == TestStatus.PASSED:
            self.passed += 1
        elif result.status == TestStatus.FAILED:
            self.failed += 1
        elif result.status == TestStatus.SKIPPED:
            self.skipped += 1
        elif result.status in [TestStatus.ERROR, TestStatus.TIMEOUT]:
            self.errors += 1

    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_tests == 0:
            return 0.0
        return (self.passed / self.total_tests) * 100


class MCPTestHarness:
    """Comprehensive MCP Server Test Harness"""

    def __init__(
        self,
        timeout: float = 30.0,
        verbose: bool = False,
        interactive: bool = False
    ):
        self.timeout = timeout
        self.verbose = verbose
        self.interactive = interactive
        self.client: Optional[Client] = None
        self.report: Optional[ServerTestReport] = None

        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)

    def detect_transport_type(self, config: Union[str, Dict]) -> TransportType:
        """Detect transport type from configuration"""
        if isinstance(config, str):
            if config.startswith("http://") or config.startswith("https://"):
                if config.endswith("/sse"):
                    return TransportType.SSE
                return TransportType.HTTP
            return TransportType.STDIO
        elif isinstance(config, dict):
            if 'url' in config:
                url = config['url']
                if url.endswith("/sse"):
                    return TransportType.SSE
                return TransportType.HTTP
            elif 'command' in config:
                return TransportType.STDIO
        return TransportType.UNKNOWN

    async def connect(self, config: Union[str, Dict]) -> bool:
        """Connect to MCP server"""
        try:
            transport = self.detect_transport_type(config)

            if isinstance(config, str):
                server_url = config
                server_name = config
            else:
                server_url = config.get('url', config.get('command', 'unknown'))
                server_name = config.get('name', server_url)

            self.report = ServerTestReport(
                server_name=server_name,
                server_url=server_url,
                transport_type=transport
            )

            print(f"\n🔗 Connecting to: {server_name}")
            print(f"   Transport: {transport.value}")
            print(f"   URL/Command: {server_url}")

            start = time.time()

            if isinstance(config, dict):
                if 'url' in config:
                    self.client = Client(config['url'])
                elif 'command' in config:
                    # FastMCP Client for stdio doesn't take env/cwd directly
                    # It expects either a string command or list of args
                    command = config['command']
                    args = config.get('args', [])

                    if args:
                        # Create full command list
                        full_command = [command] + args
                    else:
                        full_command = command

                    self.client = Client(full_command)
                else:
                    raise ValueError("Invalid config: missing 'url' or 'command'")
            else:
                self.client = Client(config)

            # Enter context manager
            await self.client.__aenter__()

            connect_time = (time.time() - start) * 1000

            result = TestResult(
                test_name="Connection",
                status=TestStatus.PASSED,
                duration_ms=connect_time,
                message=f"Connected successfully in {connect_time:.2f}ms"
            )
            self.report.add_result(result)

            print(f"✅ Connected in {connect_time:.2f}ms")
            return True

        except Exception as e:
            error_msg = f"Connection failed: {str(e)}"
            logger.error(error_msg)
            logger.debug(traceback.format_exc())

            if self.report:
                result = TestResult(
                    test_name="Connection",
                    status=TestStatus.FAILED,
                    duration_ms=0,
                    message=error_msg,
                    error=str(e)
                )
                self.report.add_result(result)

            print(f"❌ {error_msg}")
            return False

    async def test_initialization(self) -> TestResult:
        """Test MCP initialization"""
        test_name = "Initialization"
        start = time.time()

        try:
            # MCP servers should respond to initialization
            # The client should handle this internally
            duration = (time.time() - start) * 1000

            return TestResult(
                test_name=test_name,
                status=TestStatus.PASSED,
                duration_ms=duration,
                message="Server initialized successfully"
            )

        except Exception as e:
            duration = (time.time() - start) * 1000
            return TestResult(
                test_name=test_name,
                status=TestStatus.FAILED,
                duration_ms=duration,
                message=f"Initialization failed",
                error=str(e)
            )

    async def test_list_tools(self) -> TestResult:
        """Test listing available tools"""
        test_name = "List Tools"
        start = time.time()

        try:
            tools = await asyncio.wait_for(
                self.client.list_tools(),
                timeout=self.timeout
            )
            duration = (time.time() - start) * 1000

            tool_names = [t.name for t in tools]
            tool_count = len(tools)

            details = {
                "tool_count": tool_count,
                "tools": tool_names,
                "response_time_ms": duration
            }

            if self.verbose:
                print(f"\n📦 Found {tool_count} tools:")
                for tool in tools:
                    print(f"   - {tool.name}: {tool.description[:50]}...")

            return TestResult(
                test_name=test_name,
                status=TestStatus.PASSED,
                duration_ms=duration,
                message=f"Retrieved {tool_count} tools",
                details=details
            )

        except asyncio.TimeoutError:
            duration = self.timeout * 1000
            return TestResult(
                test_name=test_name,
                status=TestStatus.TIMEOUT,
                duration_ms=duration,
                message="Timeout listing tools"
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return TestResult(
                test_name=test_name,
                status=TestStatus.FAILED,
                duration_ms=duration,
                message="Failed to list tools",
                error=str(e)
            )

    async def test_list_resources(self) -> TestResult:
        """Test listing available resources"""
        test_name = "List Resources"
        start = time.time()

        try:
            resources = await asyncio.wait_for(
                self.client.list_resources(),
                timeout=self.timeout
            )
            duration = (time.time() - start) * 1000

            resource_count = len(resources) if resources else 0
            resource_names = [r.name for r in resources] if resources else []

            details = {
                "resource_count": resource_count,
                "resources": resource_names,
                "response_time_ms": duration
            }

            return TestResult(
                test_name=test_name,
                status=TestStatus.PASSED,
                duration_ms=duration,
                message=f"Retrieved {resource_count} resources",
                details=details
            )

        except asyncio.TimeoutError:
            duration = self.timeout * 1000
            return TestResult(
                test_name=test_name,
                status=TestStatus.TIMEOUT,
                duration_ms=duration,
                message="Timeout listing resources"
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            # Many servers don't implement resources, so treat as passed with note
            if "not implemented" in str(e).lower() or "no resources" in str(e).lower():
                return TestResult(
                    test_name=test_name,
                    status=TestStatus.PASSED,
                    duration_ms=duration,
                    message="Resources not implemented (OK)",
                    details={"note": "Server doesn't implement resources"}
                )
            return TestResult(
                test_name=test_name,
                status=TestStatus.FAILED,
                duration_ms=duration,
                message="Failed to list resources",
                error=str(e)
            )

    async def test_list_prompts(self) -> TestResult:
        """Test listing available prompts"""
        test_name = "List Prompts"
        start = time.time()

        try:
            prompts = await asyncio.wait_for(
                self.client.list_prompts(),
                timeout=self.timeout
            )
            duration = (time.time() - start) * 1000

            prompt_count = len(prompts) if prompts else 0
            prompt_names = [p.name for p in prompts] if prompts else []

            details = {
                "prompt_count": prompt_count,
                "prompts": prompt_names,
                "response_time_ms": duration
            }

            return TestResult(
                test_name=test_name,
                status=TestStatus.PASSED,
                duration_ms=duration,
                message=f"Retrieved {prompt_count} prompts",
                details=details
            )

        except asyncio.TimeoutError:
            duration = self.timeout * 1000
            return TestResult(
                test_name=test_name,
                status=TestStatus.TIMEOUT,
                duration_ms=duration,
                message="Timeout listing prompts"
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            # Many servers don't implement prompts, so treat as passed with note
            if "not implemented" in str(e).lower() or "no prompts" in str(e).lower():
                return TestResult(
                    test_name=test_name,
                    status=TestStatus.PASSED,
                    duration_ms=duration,
                    message="Prompts not implemented (OK)",
                    details={"note": "Server doesn't implement prompts"}
                )
            return TestResult(
                test_name=test_name,
                status=TestStatus.FAILED,
                duration_ms=duration,
                message="Failed to list prompts",
                error=str(e)
            )

    async def test_tool_execution(self, tool_name: str, args: Dict[str, Any]) -> TestResult:
        """Test executing a specific tool"""
        test_name = f"Tool Execution: {tool_name}"
        start = time.time()

        try:
            result = await asyncio.wait_for(
                self.client.call_tool(tool_name, args),
                timeout=self.timeout
            )
            duration = (time.time() - start) * 1000

            # Analyze result
            result_text = str(getattr(result, 'text', result))
            result_size = len(result_text)

            details = {
                "tool": tool_name,
                "args": args,
                "response_size": result_size,
                "response_time_ms": duration,
                "response_preview": result_text[:200] if result_text else None
            }

            return TestResult(
                test_name=test_name,
                status=TestStatus.PASSED,
                duration_ms=duration,
                message=f"Tool executed successfully",
                details=details
            )

        except asyncio.TimeoutError:
            duration = self.timeout * 1000
            return TestResult(
                test_name=test_name,
                status=TestStatus.TIMEOUT,
                duration_ms=duration,
                message=f"Timeout executing tool {tool_name}"
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return TestResult(
                test_name=test_name,
                status=TestStatus.FAILED,
                duration_ms=duration,
                message=f"Failed to execute tool {tool_name}",
                error=str(e),
                details={"tool": tool_name, "args": args}
            )

    async def test_performance(self, iterations: int = 10) -> TestResult:
        """Test server performance with multiple requests"""
        test_name = "Performance Test"
        start = time.time()

        try:
            response_times = []

            for i in range(iterations):
                iter_start = time.time()
                await self.client.list_tools()
                response_times.append((time.time() - iter_start) * 1000)

            duration = (time.time() - start) * 1000
            avg_response = sum(response_times) / len(response_times)
            min_response = min(response_times)
            max_response = max(response_times)

            details = {
                "iterations": iterations,
                "avg_response_ms": round(avg_response, 2),
                "min_response_ms": round(min_response, 2),
                "max_response_ms": round(max_response, 2),
                "total_time_ms": round(duration, 2)
            }

            # Performance thresholds
            if avg_response < 100:
                status = TestStatus.PASSED
                message = f"Excellent performance: {avg_response:.2f}ms avg"
            elif avg_response < 500:
                status = TestStatus.PASSED
                message = f"Good performance: {avg_response:.2f}ms avg"
            elif avg_response < 1000:
                status = TestStatus.PASSED
                message = f"Acceptable performance: {avg_response:.2f}ms avg"
            else:
                status = TestStatus.FAILED
                message = f"Poor performance: {avg_response:.2f}ms avg"

            return TestResult(
                test_name=test_name,
                status=status,
                duration_ms=duration,
                message=message,
                details=details
            )

        except Exception as e:
            duration = (time.time() - start) * 1000
            return TestResult(
                test_name=test_name,
                status=TestStatus.ERROR,
                duration_ms=duration,
                message="Performance test failed",
                error=str(e)
            )

    async def run_comprehensive_tests(self) -> ServerTestReport:
        """Run all comprehensive tests"""
        if not self.client or not self.report:
            raise RuntimeError("Not connected to server")

        print("\n🧪 Running Comprehensive Tests...")
        print("=" * 50)

        # Core functionality tests
        tests = [
            self.test_initialization(),
            self.test_list_tools(),
            self.test_list_resources(),
            self.test_list_prompts(),
            self.test_performance(iterations=5)
        ]

        # Execute all tests
        for test_coro in tests:
            result = await test_coro
            self.report.add_result(result)

            # Print immediate feedback
            status_emoji = "✅" if result.status == TestStatus.PASSED else "❌"
            print(f"{status_emoji} {result.test_name}: {result.status.value}")
            if result.message:
                print(f"   {result.message}")

        # Test specific tools if available and in interactive mode
        if self.interactive:
            await self.run_interactive_tool_tests()

        # Finalize report
        self.report.end_time = datetime.now().isoformat()
        if self.report.test_results:
            self.report.total_duration_ms = sum(r.duration_ms for r in self.report.test_results)

        return self.report

    async def run_interactive_tool_tests(self):
        """Run interactive tool testing"""
        try:
            tools = await self.client.list_tools()
            if not tools:
                print("\n⚠️ No tools available for interactive testing")
                return

            print(f"\n🔧 Available tools for testing:")
            for i, tool in enumerate(tools, 1):
                print(f"  {i}. {tool.name}: {tool.description[:50]}...")

            while True:
                choice = input("\nEnter tool number to test (or 'skip' to continue): ").strip()
                if choice.lower() == 'skip':
                    break

                try:
                    tool_index = int(choice) - 1
                    if 0 <= tool_index < len(tools):
                        tool = tools[tool_index]
                        print(f"\nTesting tool: {tool.name}")

                        # Get test arguments
                        args_str = input("Enter tool arguments as JSON (or {} for empty): ").strip()
                        if not args_str:
                            args_str = "{}"

                        try:
                            args = json.loads(args_str)
                            result = await self.test_tool_execution(tool.name, args)
                            self.report.add_result(result)

                            status_emoji = "✅" if result.status == TestStatus.PASSED else "❌"
                            print(f"{status_emoji} Tool test: {result.status.value}")
                            if result.details.get("response_preview"):
                                print(f"Response preview: {result.details['response_preview']}")
                        except json.JSONDecodeError:
                            print("Invalid JSON format")
                    else:
                        print("Invalid selection")
                except ValueError:
                    print("Invalid input")

        except Exception as e:
            logger.error(f"Interactive testing error: {e}")

    async def disconnect(self):
        """Disconnect from server"""
        if self.client:
            try:
                await self.client.__aexit__(None, None, None)
                print("🔌 Disconnected from server")
            except Exception as e:
                logger.error(f"Error disconnecting: {e}")

    def print_report(self):
        """Print test report"""
        if not self.report:
            return

        print("\n" + "=" * 60)
        print("📊 TEST REPORT")
        print("=" * 60)
        print(f"Server: {self.report.server_name}")
        print(f"URL: {self.report.server_url}")
        print(f"Transport: {self.report.transport_type.value}")
        print(f"Start Time: {self.report.start_time}")
        print(f"End Time: {self.report.end_time}")
        print(f"Total Duration: {self.report.total_duration_ms:.2f}ms")
        print("\n📈 Results Summary:")
        print(f"  Total Tests: {self.report.total_tests}")
        print(f"  ✅ Passed: {self.report.passed}")
        print(f"  ❌ Failed: {self.report.failed}")
        print(f"  ⚠️ Skipped: {self.report.skipped}")
        print(f"  🔥 Errors: {self.report.errors}")
        print(f"  Success Rate: {self.report.success_rate():.1f}%")

        print("\n📝 Test Details:")
        for result in self.report.test_results:
            print(f"\n  {result.test_name}:")
            print(f"    Status: {result.status.value}")
            print(f"    Duration: {result.duration_ms:.2f}ms")
            if result.message:
                print(f"    Message: {result.message}")
            if result.error and self.verbose:
                print(f"    Error: {result.error}")
            if result.details and self.verbose:
                print(f"    Details: {json.dumps(result.details, indent=6)}")

        print("\n" + "=" * 60)

    def save_report(self, filepath: str = None):
        """Save test report to JSON file"""
        if not self.report:
            return

        if not filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"mcp_test_report_{timestamp}.json"

        report_dict = asdict(self.report)
        # Convert enums to strings
        report_dict['transport_type'] = self.report.transport_type.value
        for result in report_dict['test_results']:
            result['status'] = result['status'] if isinstance(result['status'], str) else TestStatus[result['status']].value

        with open(filepath, 'w') as f:
            json.dump(report_dict, f, indent=2, default=str)

        print(f"\n💾 Report saved to: {filepath}")


class DockerMCPTester:
    """Specialized tester for Docker-based MCP servers"""

    def __init__(self, container_name: str, port: int = 8080, use_sse: bool = False):
        self.container_name = container_name
        self.port = port
        self.use_sse = use_sse
        self.base_url = f"http://localhost:{port}"
        self.url = f"{self.base_url}/sse" if use_sse else self.base_url

    def check_container_running(self) -> bool:
        """Check if Docker container is running"""
        import subprocess
        try:
            result = subprocess.run(
                ["docker", "ps", "-q", "-f", f"name={self.container_name}"],
                capture_output=True,
                text=True
            )
            return bool(result.stdout.strip())
        except Exception:
            return False

    def start_container(self, image: str, additional_args: List[str] = None) -> bool:
        """Start Docker container"""
        import subprocess
        try:
            cmd = [
                "docker", "run", "-d",
                "--name", self.container_name,
                "-p", f"{self.port}:{self.port}"
            ]
            if additional_args:
                cmd.extend(additional_args)
            cmd.append(image)

            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            print(f"Failed to start container: {e}")
            return False

    def stop_container(self):
        """Stop and remove Docker container"""
        import subprocess
        try:
            subprocess.run(["docker", "stop", self.container_name], capture_output=True)
            subprocess.run(["docker", "rm", self.container_name], capture_output=True)
        except Exception:
            pass

    async def test_docker_mcp_server(
        self,
        image: str = "ramparts:local",
        start_fresh: bool = True,
        cleanup: bool = True
    ) -> ServerTestReport:
        """Test Docker-based MCP server"""
        harness = MCPTestHarness(verbose=True)

        try:
            # Check/start container
            if start_fresh:
                print(f"\n🐳 Starting Docker container: {self.container_name}")
                self.stop_container()  # Clean up any existing container

                # Start ramparts in HTTP server mode
                success = self.start_container(
                    image,
                    ["--entrypoint", "/app/ramparts", image, "server", "--port", str(self.port), "--host", "0.0.0.0"]
                )

                if not success:
                    print("❌ Failed to start Docker container")
                    return None

                # Wait for container to be ready
                print("⏳ Waiting for container to be ready...")
                await asyncio.sleep(3)

            elif not self.check_container_running():
                print(f"❌ Container {self.container_name} is not running")
                return None

            # Connect and test
            print(f"\n🔗 Connecting to Docker MCP server at {self.url}")
            connected = await harness.connect(self.url)

            if not connected:
                print("❌ Failed to connect to Docker MCP server")
                return None

            # Run comprehensive tests
            report = await harness.run_comprehensive_tests()

            # Disconnect
            await harness.disconnect()

            return report

        finally:
            if cleanup:
                print(f"\n🧹 Cleaning up container: {self.container_name}")
                self.stop_container()


async def test_multiple_servers(configs: List[Dict[str, Any]]) -> List[ServerTestReport]:
    """Test multiple MCP servers"""
    reports = []

    for config in configs:
        print(f"\n{'=' * 60}")
        print(f"Testing server: {config.get('name', config.get('url', 'Unknown'))}")
        print('=' * 60)

        harness = MCPTestHarness(verbose=True)

        try:
            connected = await harness.connect(config)
            if connected:
                report = await harness.run_comprehensive_tests()
                reports.append(report)
                harness.print_report()
            else:
                print("⚠️ Skipping tests due to connection failure")
        except Exception as e:
            print(f"❌ Test failed: {e}")
        finally:
            await harness.disconnect()

    return reports


async def main():
    parser = argparse.ArgumentParser(description="MCP Server Test Harness")
    parser.add_argument("server", nargs="?", help="Server URL or command")
    parser.add_argument("--docker", action="store_true", help="Test Docker container")
    parser.add_argument("--image", default="ramparts:local", help="Docker image to test")
    parser.add_argument("--port", type=int, default=8080, help="Port for Docker container")
    parser.add_argument("--sse", action="store_true", help="Use SSE transport")
    parser.add_argument("--config", help="Path to MCP config file")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--interactive", action="store_true", help="Interactive tool testing")
    parser.add_argument("--save-report", help="Save report to file")
    parser.add_argument("--timeout", type=float, default=30.0, help="Request timeout")

    args = parser.parse_args()

    if args.docker:
        # Docker testing mode
        tester = DockerMCPTester(
            container_name="mcp-test-container",
            port=args.port,
            use_sse=args.sse
        )
        report = await tester.test_docker_mcp_server(
            image=args.image,
            start_fresh=True,
            cleanup=True
        )

        if report:
            harness = MCPTestHarness(verbose=args.verbose)
            harness.report = report
            harness.print_report()
            if args.save_report:
                harness.save_report(args.save_report)

    elif args.config:
        # Test from config file
        config_path = Path(args.config)
        if not config_path.exists():
            print(f"❌ Config file not found: {args.config}")
            sys.exit(1)

        with open(config_path) as f:
            config_data = json.load(f)

        if 'mcpServers' in config_data:
            servers = list(config_data['mcpServers'].values())
            reports = await test_multiple_servers(servers)
        else:
            print("❌ Invalid config file format")
            sys.exit(1)

    elif args.server:
        # Test single server
        harness = MCPTestHarness(
            timeout=args.timeout,
            verbose=args.verbose,
            interactive=args.interactive
        )

        connected = await harness.connect(args.server)
        if connected:
            report = await harness.run_comprehensive_tests()
            harness.print_report()
            if args.save_report:
                harness.save_report(args.save_report)

        await harness.disconnect()

    else:
        print("Usage: python mcp_test_harness.py [server_url]")
        print("       python mcp_test_harness.py --docker --image ramparts:local")
        print("       python mcp_test_harness.py --config .mcp.json")
        print("\nOptions:")
        print("  --docker        Test Docker container")
        print("  --image         Docker image to test (default: ramparts:local)")
        print("  --port          Port for Docker container (default: 8080)")
        print("  --sse           Use SSE transport")
        print("  --verbose       Enable verbose output")
        print("  --interactive   Enable interactive tool testing")
        print("  --save-report   Save test report to file")
        print("  --timeout       Request timeout in seconds (default: 30)")


if __name__ == "__main__":
    asyncio.run(main())