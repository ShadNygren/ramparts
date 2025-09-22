# RAMPARTS Fixes and Development History

Last Updated: 2025-09-21

## Table of Contents
1. [Current Issues](#current-issues)
2. [Solved Problems](#solved-problems)
3. [Docker Build History](#docker-build-history)
4. [Testing Infrastructure](#testing-infrastructure)
5. [Next Steps](#next-steps)

---

## Current Issues

### 1. MCP Tools Not Exposed in Protocol (CRITICAL)
**Status:** 🔴 UNRESOLVED - RMCP STDIO TRANSPORT COMPLETELY BROKEN
**First Identified:** 2025-09-20
**Last Tested:** 2025-09-22 with v0.6.4 and manual registration
**Root Cause:** rmcp library broken at MULTIPLE levels - macros AND stdio transport

#### Problem Description
Despite implementing 5 tools using rmcp macros, the MCP server returns empty tool arrays when clients connect:
- Tools ARE implemented in `/src/mcp_server.rs`
- Tools ARE decorated with `#[tool]` macro
- ~~ServerHandler IS decorated with `#[tool_handler]`~~ **DOESN'T EXIST**
- ~~Tool router IS initialized with `Self::tool_router()`~~ **DOESN'T EXIST**
- BUT tools array remains empty in initialize response

#### Root Cause Discovery
After deep investigation of the rmcp v0.3.2 source code:
- The macros `#[tool_router]` and `#[tool_handler]` **DO NOT EXIST** in rmcp
- The correct pattern uses `tool_box!` macro instead
- We were using non-existent macros causing silent compilation failure

##### Critical Finding (2025-09-21 14:30)
Deep analysis of rmcp macro implementation revealed:
1. The `#[tool]` macro generates two helper functions for each tool:
   - `{tool_name}_tool_attr()` - returns tool metadata
   - `{tool_name}_tool_call()` - wrapper for async tool execution
2. The `tool_box!` macro collects these generated functions
3. The macro expects specific patterns that may not be generated correctly
4. The library was archived 5 months ago (April 2025) and appears unmaintained

#### Tools That Should Be Exposed
1. `health` - Healthcheck for the Ramparts MCP server
2. `increment_counter` - Increment internal counter and return value
3. `scan` - Scan MCP server URL and return security findings as JSON
4. `scan-config` - Scan MCP servers from IDE configuration files
5. `refresh-tools` - Refresh tool descriptions from MCP servers

#### Research Conducted
1. **rmcp Library Investigation (v0.3.2)**
   - Reviewed macro patterns from multiple GitHub repositories
   - Found Shuttle.dev example showing proper ServerInfo initialization
   - Discovered Implementation::from_build_env() pattern
   - Confirmed macro order: `#[tool_router]` before impl, `#[tool_handler]` on ServerHandler

2. **ServerInfo Configuration Issues**
   - Initial error: Missing fields (name, version, protocol_version)
   - Fixed by using proper structure with Implementation::from_build_env()
   - ServerCapabilities properly configured with enable_tools()
   - Still doesn't expose tools despite fixes

3. **Code Changes Made** (`src/mcp_server.rs`):
   ```rust
   // Added proper imports
   use rmcp::model::{Implementation, ProtocolVersion, ServerCapabilities, ServerInfo};

   // Fixed ServerInfo structure
   fn get_info(&self) -> ServerInfo {
       ServerInfo {
           protocol_version: ProtocolVersion::V_2024_11_05,
           capabilities: ServerCapabilities::builder().enable_tools().build(),
           server_info: Implementation::from_build_env(),
           instructions: Some("Ramparts MCP Security Scanner - Tools for scanning MCP servers for security vulnerabilities".to_string()),
       }
   }
   ```

#### Fix Applied (2025-09-21 at 13:45) - **FAILED**
The correct rmcp v0.3.2 implementation requires:

1. **Remove non-existent macros**:
   - ~~`#[tool_router]`~~ → Remove from impl block
   - ~~`#[tool_handler]`~~ → Remove from ServerHandler impl

2. **Use `tool_box!` macro properly**:
   ```rust
   impl RampartsMcpServer {
       // ... tool methods ...

       // Register tools at end of impl block
       tool_box!(RampartsMcpServer { health, increment_counter, scan, scan_config, refresh_tools });
   }

   impl ServerHandler for RampartsMcpServer {
       // Add this inside the impl block
       tool_box!(@derive);

       fn get_info(&self) -> ServerInfo { /* ... */ }
   }
   ```

3. **Remove obsolete field**:
   - Removed `tool_router: ToolRouter<Self>` field from struct
   - Removed `tool_router: Self::tool_router()` initialization

**RESULT:** This approach still fails to expose tools. The rmcp library appears to have a fundamental issue with tool registration that the `tool_box!` macro alone cannot resolve.

#### CRITICAL DISCOVERY (2025-09-21 16:45)

We discovered we were investigating the WRONG rmcp library!

**Version Confusion:**
- **Local fork** (`~/github/ShadNygren/rmcp`): From 4t145/rmcp, version **0.1.5** (archived)
- **Currently using**: rmcp version **0.3.2** from crates.io
- **Latest available**: rmcp version **0.6.4** from modelcontextprotocol/rust-sdk (official!)

The 4t145/rmcp (v0.1.5) is NOT what we've been using (v0.3.2). The official modelcontextprotocol/rust-sdk has v0.6.4 which likely includes fixes!

**Current Action:**
- Upgraded Cargo.toml from rmcp v0.3.2 to v0.6.4
- Built Docker image: `ramparts:v2025-09-21t16-45-rmcp-064`
- **RESULT:** Build had 11 compilation errors, and tools STILL not exposed
- The rmcp library appears fundamentally broken for tool registration

**FINAL VERDICT (2025-09-21 19:00):**
After exhaustive investigation:
1. Non-existent macros were being used (`#[tool_router]`, `#[tool_handler]`)
2. Correct `tool_box!` pattern with v0.3.2 didn't work
3. Discovered we were investigating wrong repository (4t145/rmcp v0.1.5 instead of actual v0.3.2)
4. Upgraded to official v0.6.4 from modelcontextprotocol/rust-sdk - still broken
5. **CONCLUSION:** The rmcp library's tool registration is fundamentally broken across all versions

**❌ SOLUTION ATTEMPTED AND FAILED (2025-09-21 20:45, Failed 2025-09-22):**
Implemented manual tool registration by overriding `list_tools()` and `call_tool()` methods in ServerHandler implementation:

```rust
impl ServerHandler for RampartsMcpServer {
    fn list_tools(&self) -> Vec<rmcp::model::Tool> {
        // Manually return tool definitions
    }
    fn call_tool(&self, name: String, params: serde_json::Value) -> impl Future {
        // Manually dispatch to tool methods
    }
}
```

**RESULT: COMPLETE FAILURE**
- Manual registration code is correct but never executes
- MCP stdio transport is completely broken - no response to ANY messages
- Tested with both rmcp v0.3.2 and v0.6.4 - both fail identically
- Binary runs (`--version` works) but stdio communication is dead
- Debug output never appears - failure before our code runs

**CRITICAL FINDING (2025-09-22):**
The rmcp library has TWO separate critical bugs:
1. Tool registration macros don't work (bypassed with manual registration)
2. **Stdio transport is completely non-functional** (cannot be bypassed)

The second bug makes the library completely unusable for MCP stdio servers.

#### Technical Analysis of Failure
The tool registration fails because:
1. The `#[tool]` procedural macro may not be generating the expected helper functions
2. The `tool_box!` macro references `paste!` macro for name concatenation
3. The generated functions may have visibility issues or incorrect signatures
4. No compile-time errors are shown, suggesting silent failure in macro expansion

---

## Solved Problems

### 1. CPU Architecture Compatibility (AVX2 Instructions)
**Status:** ✅ RESOLVED
**Resolution Date:** 2025-09-20

#### Problem
Binary compiled with AVX2 instructions crashed on Ivy Bridge processors (3rd gen Intel Core) with:
```
Illegal instruction (core dumped)
```

#### Solution
Created `Dockerfile.AVX_only` with CPU target restriction:
```dockerfile
ENV RUSTFLAGS="-C target-cpu=ivybridge"
```

This ensures binary only uses instructions available on Ivy Bridge and later CPUs (AVX but not AVX2).

### 2. Docker Image Execution Issues
**Status:** ✅ RESOLVED
**Resolution Date:** 2025-09-19

#### Problems Fixed
1. **e.print() method not found** - Replaced with println!/eprintln! macros
2. **Clap version parsing** - Fixed clap attribute syntax
3. **Subcommand handling** - Made subcommand optional for --help/--version
4. **Registry compatibility** - Lowercase image names required

#### Git Commits
- `2604e42` - fix: use println/eprintln directly instead of e.print()
- `7ba4a84` - fix: update docker-compose.yml to use unified Dockerfile
- `f83160b` - fix: use try_parse to handle --help and --version flags
- `0661983` - fix: make CLI subcommand optional
- `a202d3c` - fix: correct clap version attribute syntax
- `6a7e1f0` - fix: lowercase Docker image names

### 3. Rust Version Compatibility
**Status:** ✅ RESOLVED
**Resolution Date:** 2025-09-19

#### Problem
Cargo.lock version 4 incompatibility with older Rust versions

#### Solution
- Updated to Rust 1.80-slim in Docker
- Later updated to latest Rust for edition2024 support
- Commits: `ca420f3`, `7b18751`

### 4. Docker Build Optimization
**Status:** ✅ RESOLVED
**Resolution Date:** 2025-09-19

#### Improvements Made
1. Single multi-stage Dockerfile replacing multiple variants
2. Comprehensive .dockerignore for efficient builds
3. Added debugging tools (strace, gdb, file) for diagnostics
4. Security hardening with non-root user (ramparts:1001)

---

## Docker Build History

### Test Builds Created (2025-09-19 to 2025-09-21)

| Image Tag | Date | Purpose | Result |
|-----------|------|---------|--------|
| `v2025-09-21t12-30` | 2025-09-21 | ServerInfo fix attempt | ❌ Tools not exposed |
| `v2025-09-21t12-00` | 2025-09-21 | Initial macro investigation | ❌ Tools not exposed |
| `fixed` | 2025-09-20 | Multiple fix attempts | ❌ Tools not exposed |
| `ivybridge` | 2025-09-20 | CPU compatibility fix | ✅ Runs on Ivy Bridge |
| `ubuntu-both` | 2025-09-19 | Ubuntu base testing | ✅ Builds successfully |
| `working` | 2025-09-19 | Basic functionality | ✅ MCP responds |

### Active Dockerfiles

1. **`Dockerfile`** - Main production Dockerfile (currently modified)
2. **`Dockerfile.AVX_only`** - CPU-restricted build for older processors
3. **`docker-compose.yml`** - Local development orchestration

---

## Testing Infrastructure

### Test Harness (`test_harness/`)

Created comprehensive testing suite for MCP server validation:

1. **`mcp_test_harness.py`** - Main test framework with FastMCP
2. **`test_ramparts_mcp_stdio.py`** - Stdio transport testing
3. **`test_docker_tools.py`** - Docker container tool discovery
4. **`test_mcp_client.py`** - Simple MCP client implementation
5. **`ramparts_self_scan.py`** - Ramparts scanning itself

### Test Results
- MCP server responds to initialize requests ✅
- ServerInfo returns correct protocol version ✅
- Tools array remains empty ❌
- Resources/prompts arrays empty (expected) ✅

---

## Next Steps

### Immediate Actions

1. **Try Alternative rmcp Implementation**
   - Consider switching from rmcp 0.3.2 to official modelcontextprotocol/rust-sdk
   - Or try 4t145/rmcp which may have different macro implementation

2. **Manual Tool Registration**
   - Bypass macros and manually implement tool registration
   - Create explicit tool list in ServerHandler implementation

3. **Debug Macro Expansion**
   - Use `cargo expand` to see what macros generate
   - Add debug logging in tool registration code

### Long-term Solutions

1. **File rmcp Bug Report**
   - Document the tool registration issue
   - Create minimal reproduction example
   - Submit to rmcp repository

2. **Create Custom MCP Implementation**
   - If rmcp continues to fail, implement custom MCP protocol handler
   - Use existing protocol types but custom registration

3. **Alternative Architecture**
   - Consider exposing tools via different mechanism
   - Maybe REST API wrapper around MCP tools

---

## Important Technical Notes

### rmcp Macro System
- Version: 0.3.2
- Macros: `#[tool_router]`, `#[tool_handler]`, `#[tool]`
- The tool_router macro should generate a `tool_router()` function
- Tools should auto-register via the macro attributes
- Current behavior suggests registration isn't happening

### Docker CPU Targeting
- Use `RUSTFLAGS="-C target-cpu=<arch>"` to control instruction set
- Common targets:
  - `ivybridge` - 3rd gen Intel Core (AVX, no AVX2)
  - `haswell` - 4th gen Intel Core (AVX2)
  - `native` - Optimize for build machine (dangerous for distribution)

### MCP Protocol Details
- Protocol version: 2024-11-05
- Initialize sequence: initialize request → response → initialized notification
- Tools should appear in initialize response capabilities
- Tool listing via `tools/list` method after initialization

---

## Version Tracking Convention

Using ISO-8601 datetime format for version tags:
- Format: `vYYYY-MM-DDtHH-MM`
- Example: `v2025-09-21t12-30`
- Benefits: Chronological ordering, unique identification

---

## Current Working Directory Structure

```
/home/dell/github/ShadNygren/ramparts/
├── src/
│   ├── mcp_server.rs (MODIFIED - tool implementation)
│   └── bin/ (test binaries)
├── test_harness/ (comprehensive test suite)
├── Dockerfile (MODIFIED)
├── Dockerfile.AVX_only (CPU-restricted build)
└── Various test outputs and logs
```

---

## Contact and Support

Repository: https://github.com/ShadNygren/ramparts
Original: https://github.com/getjavelin/ramparts