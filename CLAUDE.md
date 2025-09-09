# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Ramparts** is a security scanner for Model Context Protocol (MCP) servers written in Rust. It analyzes MCP endpoints to identify available tools, resources, and potential security vulnerabilities including tool poisoning, injection attacks, and data leakage.

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
make ci-check
```

### Running the Application
```bash
# Scan a single MCP server
cargo run -- scan http://localhost:3000

# Scan IDE configurations (discovers from Cursor, VS Code, etc.)
cargo run -- scan-config

# Start as HTTP microservice
cargo run -- server --port 3000

# Run as MCP server (stdio transport)
cargo run -- mcp-stdio

# Initialize configuration file
cargo run -- init-config
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
- **`src/server.rs`**: HTTP microservice for continuous monitoring
- **`src/config.rs`**: Configuration management for scanner settings and security rules
- **`src/types.rs`**: Core data structures and scan options
- **`src/utils.rs`**: Utility functions for output formatting and reporting

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
- Unit tests embedded in modules
- Integration tests in `src/integration_tests.rs`
- CI tests via `make ci-check`

### Common Test Patterns
- Mock MCP servers for transport testing
- Configuration validation tests
- Security assessment rule verification

## Code Style

- **Formatting**: Enforced via `cargo fmt`
- **Linting**: Comprehensive clippy rules with pedantic checks
- **Line Length**: Extended to 150 lines for complex configuration parsing (see `clippy.toml`)
- **Async Patterns**: Heavy use of tokio async/await throughout

## Security Considerations

- Never log sensitive authentication headers or tokens
- Validate all URL inputs to prevent SSRF
- Sanitize file paths to prevent directory traversal
- Use TLS for all external HTTP connections (`rustls-tls` feature)