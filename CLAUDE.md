# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ CRITICAL BUILD REQUIREMENT

**ONLY use GitHub Actions for building Docker images and Rust binaries!**

DO NOT use local Docker builds on development machines due to CPU instruction set incompatibilities. The development laptop has an Intel Ivy Bridge CPU (no AVX2 support) which causes silent failures when Rust dependencies are compiled with modern CPU optimizations.

All builds MUST be done via GitHub Actions which have modern CPUs with full instruction set support.

## Project Overview

**Ramparts** is a security scanner for Model Context Protocol (MCP) servers written in Rust. It analyzes MCP endpoints to identify available tools, resources, and potential security vulnerabilities including tool poisoning, injection attacks, and data leakage.

### Critical Security Context

Industry research revealed that **23% of public MCP servers contain command injection vulnerabilities** (May 2025), and a critical vulnerability in the official GitHub MCP integration allowed attackers to hijack AI agents through prompt injection. Ramparts addresses these urgent security needs by providing comprehensive vulnerability detection for the MCP ecosystem.

## Development Commands

### Building and Testing
```bash
# Build with quality checks (formatting, clippy, build)
make build

# Build for current architecture only (faster for development)
cargo build --release

# Run tests
cargo test --all-features
make test

# Run individual test files
cargo test --test integration_tests

# Format code
make fmt
cargo fmt

# Format check (CI verification)
cargo fmt --all -- --check
make fmt-check

# Lint with clippy
make lint
cargo clippy --all-features -- -D warnings

# Check code without building
make check
cargo check --all-features

# Audit dependencies
make audit
cargo audit

# Full CI quality checks (run before PR)
make ci-check  # Includes format, clippy, tests, audit
```

### Running the Application
```bash
# Scan a single MCP server
cargo run -- scan http://localhost:3000
cargo run -- scan http://localhost:3000 --format json

# With authentication headers
cargo run -- scan https://api.example.com/mcp --auth-headers "Authorization: Bearer TOKEN"

# Scan IDE configurations (discovers from Cursor, VS Code, Windsurf, etc.)
cargo run -- scan-config
cargo run -- scan-config --format json --report

# Start as HTTP microservice
cargo run -- server --port 3000 --host 0.0.0.0

# Run as MCP server (stdio transport)
cargo run -- mcp-stdio

# Run as MCP server (SSE transport)
cargo run -- mcp-sse --port 8000

# Run as MCP server (HTTP streamable transport)
cargo run -- mcp-http --port 8081

# Start proxy with Javelin Guardrails
cargo run -- proxy 127.0.0.1:8080

# Initialize configuration file
cargo run -- init-config [--force]
```

### Multi-Architecture Builds
The project supports cross-compilation via the comprehensive Makefile:
```bash
# Build for specific targets
make build-linux-x86_64
make build-macos-aarch64
make build-windows-x86_64-msvc

# Build for all targets
make build-all

# Create distribution packages
make package
```

## Architecture

### Core Components

- **`src/main.rs`**: CLI entry point with command parsing and routing
- **`src/scanner.rs`**: Core MCP scanning logic and client transport handling
- **`src/mcp_client.rs`**: MCP protocol client implementation supporting HTTP, SSE, and stdio transports
- **`src/mcp_server.rs`**: MCP server implementation (Ramparts as an MCP server)
- **`src/security/`**: Security analysis modules including YARA-based static analysis and LLM-powered assessments
- **`src/server.rs`**: HTTP microservice for continuous monitoring (Axum-based)
- **`src/config.rs`**: Configuration management for scanner settings and security rules
- **`src/types.rs`**: Core data structures and scan options
- **`src/utils.rs`**: Utility functions for output formatting and reporting
- **`src/cache.rs`**: Caching layer for scan results
- **`common/`**: Shared utilities between main and proxy modules (255 lines)
- **`proxy/`**: MCP proxy implementation with Javelin Guardrails integration

### Security Analysis Pipeline

1. **Discovery**: Connects to MCP servers via multiple transports (HTTP, SSE, stdio)
2. **Enumeration**: Discovers available tools, resources, and prompts
3. **Static Analysis**: YARA-based pattern matching for known vulnerabilities
4. **Dynamic Analysis**: LLM-powered assessment of security implications
5. **Risk Assessment**: Categorizes findings by severity (CRITICAL, HIGH, MEDIUM, LOW)

### Transport Support

The scanner supports multiple MCP transport protocols:
- **HTTP**: Standard REST API endpoints
- **SSE**: Server-Sent Events for streaming
- **stdio**: Standard input/output for subprocess communication
- **subprocess**: Direct process spawning with command arguments

## Configuration

### Scanner Configuration (`config.yaml`)
Generated via `ramparts init-config`, controls:
- HTTP/scan timeouts
- Output formatting preferences  
- Security assessment settings
- LLM integration configuration
- Custom YARA rule paths

### IDE Integration
Automatically discovers MCP server configurations from:
- VS Code: `~/.vscode/mcp.json`
- Cursor: `~/.cursor/mcp.json`
- Windsurf: `~/.codeium/windsurf/mcp_config.json`
- Claude Desktop: `~/Library/Application Support/Claude/claude_desktop_config.json`

## Dependencies

### Key Rust Crates
- **`rmcp`**: Official Rust MCP SDK for client/server functionality
- **`reqwest`**: HTTP client with TLS support
- **`tokio`**: Async runtime
- **`clap`**: Command-line argument parsing
- **`yara-x`**: YARA rule engine for static analysis (optional feature)
- **`axum`**: Web framework for microservice
- **`serde`**: JSON serialization
- **`tracing`**: Structured logging

### Build Features
- `default = ["yara-x-scanning"]`: Enables YARA-based security scanning
- `yara-x-scanning`: Optional static analysis capabilities

## Testing

### Test Structure
- **Unit tests**: Embedded in modules (79 test functions)
- **Integration tests**: `src/integration_tests.rs` (13 test modules)
- **CI tests**: via `make ci-check`
- **Test harness**: `test_harness/` directory with Python-based MCP testing tools

### Common Test Patterns
- Mock MCP servers for transport testing
- Configuration validation tests
- Security assessment rule verification
- FastMCP-based protocol testing

### Test Coverage Gaps
- Limited test coverage reporting (target: >80%)
- Missing end-to-end testing scenarios
- Limited mocking for external dependencies (LLM APIs)
- No dedicated security vulnerability testing

## Code Style

- **Formatting**: Enforced via `cargo fmt`
- **Linting**: Comprehensive clippy rules with pedantic checks
- **Line Length**: Extended to 150 lines for complex configuration parsing (see `clippy.toml`)
- **Async Patterns**: Heavy use of tokio async/await throughout
- **Error Handling**: Use `anyhow::Result` for main errors, `thiserror` for custom error types
- **Logging**: Use `tracing` crate with structured logging
- **Naming**: snake_case for vars/functions, PascalCase for types, SCREAMING_SNAKE for constants
- **Imports**: Group std, external crates, then local modules with blank lines between

## Docker Deployment

### Container Images
The project builds two Docker images:
- **`Dockerfile`**: MCP server mode (stdio transport) - for integration with MCP hosts
- **`Deploy-Dockerfile`**: HTTP server mode (web API) - for standalone deployments

### Quick Start with Docker
```bash
# MCP Server mode (stdio)
docker run -it ghcr.io/shadnygren/ramparts:latest

# HTTP Server mode (web API)
docker run -p 8080:8080 ghcr.io/shadnygren/ramparts-server:latest

# Docker Compose (both modes)
cp .env.example .env  # Edit with your API keys
docker-compose up
```

### Development with Docker
```bash
# Build locally
docker build -t ramparts:local .

# Development mode with Docker Compose
docker-compose --profile dev up ramparts-dev

# Test different modes
docker run --rm ramparts:local /app/ramparts --help
```

### GitHub Container Registry (GHCR)
Images automatically published to GHCR on:
- Git tags (releases): `v*.*.*`
- Main branch pushes
- `shadnygren/docker` branch pushes

Multi-architecture support: `linux/amd64`, `linux/arm64`

## Security Considerations

- Never log sensitive authentication headers or tokens
- Validate all URL inputs to prevent SSRF
- Sanitize file paths to prevent directory traversal
- Use TLS for all external HTTP connections (`rustls-tls` feature)
- Docker images run as non-root user (`ramparts:1001`)
- Environment variable injection for API keys instead of hardcoded values
- Prefer `make ci-check` before PRs (format, clippy, tests, audit)

### Critical Security Context (Industry Research)
- **23% of public MCP servers contain command injection vulnerabilities** (May 2025 research)
- Critical vulnerability in GitHub MCP integration allowed agent hijacking via prompt injection
- Widespread OAuth token leakage and authentication bypass issues in MCP ecosystem
- Ramparts addresses these real-world vulnerabilities with comprehensive security assessments

## Critical Issues and Context (2025-09-22)

### 🚨 CRITICAL FAILURE: RMCP Library Completely Broken
The rmcp library is **fundamentally broken** and cannot be used for MCP servers:

1. **Macro System Broken**: Tool registration macros don't work (tested v0.3.2 and v0.6.4)
   - Non-existent macros were referenced (`#[tool_router]`, `#[tool_handler]`)
   - Correct `tool_box!` macro also fails
   - Manual registration workaround implemented

2. **Stdio Transport Dead**: MCP server doesn't respond to ANY protocol messages
   - No response to initialize, tools/list, or any JSON-RPC messages
   - Debug output never appears - failure occurs before our code runs
   - Binary runs (`--version` exits 0) but stdio communication is completely silent

3. **All Workarounds Failed**:
   - ❌ Manual tool registration never executes (stdio fails first)
   - ❌ Upgraded to rmcp v0.6.4 - still broken
   - ❌ Used Ivy Bridge CPU compatibility - binary runs but MCP dead

**Current Status**: Project is **BLOCKED** - cannot proceed without replacing rmcp library entirely.

See RAMPARTS_FIXES.md, RMCP_MACRO_ANALYSIS.md, and MANUAL_REGISTRATION_STATUS.md for full investigation details.

### Key Technical Findings

#### rmcp Library Versions Tested
- **v0.3.2** (crates.io): Macro system broken, stdio transport dead
- **v0.6.4** (modelcontextprotocol/rust-sdk): Latest official, same failures
- **v0.1.5** (4t145/rmcp): Archived fork we mistakenly investigated

#### Docker Build Considerations
- **CPU Targeting**: Use `RUSTFLAGS="-C target-cpu=ivybridge"` for older CPUs (no AVX2)
- **Multiple Dockerfiles**: `Dockerfile.AVX_only` exists for CPU compatibility
- **Non-root user**: ramparts:1001 for security

#### Testing Infrastructure
The `test_harness/` directory contains comprehensive MCP testing tools:
- `mcp_test_harness.py` - FastMCP-based testing framework
- `test_ramparts_mcp_stdio.py` - Stdio transport testing
- `test_docker_tools.py` - Tool discovery testing

### Version Naming Convention
Using ISO-8601 datetime format for Docker image tags:
- Format: `vYYYY-MM-DDtHH-MM`
- Example: `v2025-09-21t12-30`

### Background Processes Warning
When resuming work, be aware that multiple Docker builds may be running in background. Use `docker ps` and `jobs` to check status.

### Current State (2025-09-22)

#### Code Changes
- `src/mcp_server.rs` - Manual tool registration implemented (correct but never executes)
- `Cargo.toml` - Currently using rmcp v0.6.4 (also tested v0.3.2)
- `Dockerfile.AVX_only` - CPU compatibility for Ivy Bridge

#### Docker Images Built
- `ramparts:manual-tools-v1` - rmcp v0.3.2 with manual registration
- `ramparts:v064-manual-tools` - rmcp v0.6.4 with manual registration
- Both images: Binary runs but MCP completely silent

#### Test Infrastructure
- `test_mcp_complete.py` - Comprehensive MCP protocol tester
- `test_manual_registration.py` - Manual registration verification
- All tests show: No response from MCP server
# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.