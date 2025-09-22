#!/usr/bin/env python3
"""
Direct Docker testing for Ramparts MCP Server
Generates comprehensive test report without FastMCP dependency
"""

import json
import subprocess
import time
from datetime import datetime
from typing import Dict, Any, List

class RampartsDockerTester:
    """Test Ramparts Docker image directly"""

    def __init__(self):
        self.results = []
        self.start_time = datetime.now()

    def run_docker_command(self, args: List[str], input_data: str = None, timeout: int = 10) -> Dict[str, Any]:
        """Run a docker command and return results"""
        try:
            cmd = ["docker", "run", "-i", "--rm", "ramparts:local"] + args

            process_input = input_data.encode() if input_data else None

            result = subprocess.run(
                cmd,
                input=process_input,
                capture_output=True,
                timeout=timeout
            )

            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout.decode()[:1000] if result.stdout else "",
                "stderr": result.stderr.decode()[:1000] if result.stderr else "",
                "timeout": False
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": "Command timed out",
                "timeout": True
            }
        except Exception as e:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "timeout": False
            }

    def test_container_basics(self) -> Dict[str, Any]:
        """Test basic container functionality"""
        print("\n📦 Testing Container Basics")
        print("-" * 40)

        test = {
            "name": "Container Basics",
            "tests": []
        }

        # Test 1: Container runs
        print("  Testing container execution...")
        result = subprocess.run(
            ["docker", "run", "--rm", "--entrypoint", "echo", "ramparts:local", "OK"],
            capture_output=True,
            timeout=5
        )
        container_runs = result.stdout.decode().strip() == "OK"
        test["tests"].append({
            "name": "Container runs",
            "passed": container_runs,
            "message": "✅ Container runs" if container_runs else "❌ Container fails to run"
        })
        print(f"    {'✅' if container_runs else '❌'} Container execution")

        # Test 2: Ramparts binary exists
        print("  Testing ramparts binary...")
        result = subprocess.run(
            ["docker", "run", "--rm", "--entrypoint", "ls", "ramparts:local", "/app/ramparts"],
            capture_output=True,
            timeout=5
        )
        binary_exists = result.returncode == 0
        test["tests"].append({
            "name": "Binary exists",
            "passed": binary_exists,
            "message": "✅ Binary found" if binary_exists else "❌ Binary not found"
        })
        print(f"    {'✅' if binary_exists else '❌'} Binary exists")

        # Test 3: Check binary size
        print("  Checking binary size...")
        result = subprocess.run(
            ["docker", "run", "--rm", "--entrypoint", "sh", "ramparts:local", "-c", "stat -c %s /app/ramparts"],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            size = int(result.stdout.decode().strip())
            size_ok = size > 100000  # Should be at least 100KB
            test["tests"].append({
                "name": "Binary size",
                "passed": size_ok,
                "size_bytes": size,
                "message": f"Binary size: {size/1024:.1f}KB"
            })
            print(f"    {'✅' if size_ok else '⚠️'} Binary size: {size/1024:.1f}KB")
        else:
            test["tests"].append({
                "name": "Binary size",
                "passed": False,
                "message": "Failed to check size"
            })

        return test

    def test_mcp_stdio_mode(self) -> Dict[str, Any]:
        """Test MCP stdio mode"""
        print("\n🔌 Testing MCP stdio Mode")
        print("-" * 40)

        test = {
            "name": "MCP stdio Mode",
            "tests": []
        }

        # Test 1: Initialize request
        print("  Testing MCP initialize...")
        init_request = json.dumps({
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "1.0.0",
                "capabilities": {}
            },
            "id": 1
        })

        result = self.run_docker_command([], init_request, timeout=10)

        init_success = result["success"] and not result["timeout"]
        test["tests"].append({
            "name": "MCP Initialize",
            "passed": init_success,
            "response": result.get("stdout", "")[:200],
            "message": "✅ Initialize works" if init_success else "❌ Initialize failed"
        })
        print(f"    {'✅' if init_success else '❌'} MCP Initialize")

        # Test 2: List tools request
        print("  Testing list tools...")
        tools_request = json.dumps({
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": 2
        })

        result = self.run_docker_command([], tools_request, timeout=10)

        tools_success = result["success"] and not result["timeout"]
        test["tests"].append({
            "name": "List Tools",
            "passed": tools_success,
            "response": result.get("stdout", "")[:200],
            "message": "✅ Tools list works" if tools_success else "❌ Tools list failed"
        })
        print(f"    {'✅' if tools_success else '❌'} List Tools")

        return test

    def test_ramparts_functionality(self) -> Dict[str, Any]:
        """Test Ramparts-specific functionality"""
        print("\n🛡️ Testing Ramparts Functionality")
        print("-" * 40)

        test = {
            "name": "Ramparts Features",
            "tests": []
        }

        # Test 1: YARA rules directory
        print("  Testing YARA rules...")
        result = subprocess.run(
            ["docker", "run", "--rm", "--entrypoint", "ls", "ramparts:local", "-la", "/app/rules"],
            capture_output=True,
            timeout=5
        )
        rules_exist = result.returncode == 0
        test["tests"].append({
            "name": "YARA rules",
            "passed": rules_exist,
            "message": "✅ YARA rules found" if rules_exist else "❌ YARA rules missing"
        })
        print(f"    {'✅' if rules_exist else '❌'} YARA rules directory")

        # Test 2: Check for config file
        print("  Testing configuration...")
        result = subprocess.run(
            ["docker", "run", "--rm", "--entrypoint", "sh", "ramparts:local", "-c", "ls /app/config.yaml 2>/dev/null || echo 'not found'"],
            capture_output=True,
            timeout=5
        )
        config_status = result.stdout.decode().strip()
        has_config = "not found" not in config_status
        test["tests"].append({
            "name": "Configuration",
            "passed": True,  # Config is optional
            "message": f"Config: {'present' if has_config else 'not present (OK)'}"
        })
        print(f"    ℹ️ Configuration: {'present' if has_config else 'not present (optional)'}")

        return test

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        # Calculate totals
        total_tests = 0
        passed_tests = 0

        for test_suite in self.results:
            for test in test_suite.get("tests", []):
                total_tests += 1
                if test.get("passed", False):
                    passed_tests += 1

        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        report = {
            "title": "Ramparts Docker Image Test Report",
            "timestamp": self.start_time.isoformat(),
            "duration_seconds": duration,
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": total_tests - passed_tests,
                "success_rate": round(success_rate, 1)
            },
            "test_suites": self.results,
            "environment": {
                "docker_image": "ramparts:local",
                "test_time": datetime.now().isoformat(),
                "test_harness": "docker_test_report.py"
            },
            "conclusion": self.get_conclusion(success_rate)
        }

        return report

    def get_conclusion(self, success_rate: float) -> str:
        """Generate conclusion based on success rate"""
        if success_rate >= 90:
            return "✅ EXCELLENT - The Ramparts Docker image is fully functional"
        elif success_rate >= 70:
            return "✅ GOOD - The Ramparts Docker image is mostly functional"
        elif success_rate >= 50:
            return "⚠️ FAIR - The Ramparts Docker image has some issues"
        else:
            return "❌ POOR - The Ramparts Docker image has significant issues"

    def run_all_tests(self):
        """Run all test suites"""
        print("\n" + "="*50)
        print("🚀 RAMPARTS DOCKER IMAGE COMPREHENSIVE TEST")
        print("="*50)

        # Run test suites
        self.results.append(self.test_container_basics())
        self.results.append(self.test_mcp_stdio_mode())
        self.results.append(self.test_ramparts_functionality())

        # Generate report
        report = self.generate_report()

        # Print summary
        print("\n" + "="*50)
        print("📊 TEST REPORT SUMMARY")
        print("="*50)
        print(f"Total Tests: {report['summary']['total_tests']}")
        print(f"✅ Passed: {report['summary']['passed']}")
        print(f"❌ Failed: {report['summary']['failed']}")
        print(f"📈 Success Rate: {report['summary']['success_rate']}%")
        print(f"\n{report['conclusion']}")

        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"ramparts_docker_test_report_{timestamp}.json"

        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n💾 Detailed report saved to: {report_file}")

        # Print detailed results
        print("\n📝 Detailed Results:")
        print("-" * 50)
        for suite in self.results:
            print(f"\n{suite['name']}:")
            for test in suite.get("tests", []):
                status = "✅" if test.get("passed", False) else "❌"
                print(f"  {status} {test['name']}: {test.get('message', '')}")

        return report


def main():
    """Main test runner"""
    tester = RampartsDockerTester()
    report = tester.run_all_tests()

    # Return exit code based on success rate
    if report['summary']['success_rate'] >= 70:
        return 0  # Success
    elif report['summary']['success_rate'] >= 50:
        return 1  # Partial success
    else:
        return 2  # Failure


if __name__ == "__main__":
    import sys
    sys.exit(main())