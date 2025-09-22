# Ramparts Review - September 22, 2025

## Executive Summary

This review assesses the current state of Ramparts after pulling the latest updates from upstream (12 new commits since September 11). The project has evolved significantly with the addition of proxy functionality and Javelin Guardrails integration, but fundamental issues with the MCP server implementation remain unresolved.

Ramparts is a Rust-based security scanner specifically designed for the Model Context Protocol (MCP) ecosystem, providing comprehensive security analysis by discovering capabilities, performing static analysis through YARA rules, and utilizing AI-powered analysis to detect sophisticated security vulnerabilities.

### Critical Industry Context

Research from May 2025 revealed alarming security statistics in the MCP ecosystem:
- **23% of public MCP servers contain command injection vulnerabilities**
- Critical vulnerability in GitHub MCP integration allowed agent hijacking via prompt injection
- Widespread OAuth token leakage and authentication bypass issues

These findings underscore the critical importance of Ramparts as a security tool, even with its current limitations.

## Current Branch Status

- **Branch**: `shadnygren/github-actions` (based on latest `main`)
- **Upstream**: Synced with `getjavelin/ramparts` main branch
- **Last sync**: September 22, 2025

## Major Changes Since September 11

### New Functionality Added (Upstream)

1. **Proxy Module** (`proxy/` directory)
   - Complete MCP proxy implementation with Javelin Guardrails
   - Validation service integration
   - Caching layer for performance
   - Licensing system integration
   - New binary: `ramparts-mcp-proxy-stdio`

2. **Common Module** (`common/` directory)
   - Shared functionality between main and proxy
   - 255 lines of common utilities

3. **Simplified MCP Server**
   - Reduced from 5 tools to 2 tools only:
     - `scan` - Scan MCP server URL
     - `scan-config` - Scan IDE configurations
   - Removed: health, increment_counter, refresh_tools

4. **New CLI Commands**
   - Added `Proxy` command for starting MCP proxy server
   - Added `mcp-sse` and `mcp-http` commands for different transport modes

## GitHub Actions Workflows

The repository has comprehensive CI/CD workflows:

1. **`cicd.yml`** - Main CI/CD pipeline
2. **`cron.yml`** - Scheduled builds (changed from Friday to Monday)
3. **`e2e.yml`** - End-to-end testing
4. **`pr-check.yml`** - Pull request validation (11KB - very comprehensive)
5. **`release.yml`** - Release builds for multiple platforms (Ubuntu, Windows, macOS)
6. **`docker-build.yml`** - NEW: Docker image builds (added in this branch)

### Key Observations

- Workflows build for **multiple architectures**: x86_64 on Ubuntu 24.04, Windows 2022, macOS 15
- Uses **modern GitHub Actions** with proper caching
- Includes artifact uploads and cross-platform testing
- **Docker workflow added**: Successfully builds and pushes Deploy-Dockerfile to GHCR
- **MCP-Dockerfile issue**: Fails due to missing common/proxy directories when building from source

## Critical Issues (Unchanged)

### 1. MCP Server Still Broken
Despite upstream updates, the fundamental rmcp library issues remain:
- **rmcp v0.3.2** still in use (broken macros, non-functional stdio)
- MCP server implementation won't work due to:
  - Non-existent `#[tool_router]` and `#[tool_handler]` macros
  - Broken stdio transport
  - Silent failures with no error messages

### 2. CPU Instruction Set Problem
- Local builds fail due to Ivy Bridge CPU (no AVX2 support)
- Dependencies compiled with modern CPU optimizations cause SIGILL
- **Solution**: Must use GitHub Actions for all builds

### 3. Docker Strategy Issues
- Still using separate `MCP-Dockerfile` and `Deploy-Dockerfile`
- No `docker-compose.yml` in main branch
- Docker builds not integrated into GitHub Actions

## Working Components

### ✅ Scanner Functionality
- Core scanning works well
- Multiple transport support (HTTP, SSE, stdio subprocess)
- YARA rule integration functional with 6 comprehensive rule files covering:
  - Command injection (critical given 23% vulnerability rate)
  - SQL injection and database attacks
  - Path traversal and directory access
  - Secrets leakage and API key exposure
  - Authentication bypass
  - Prompt injection (addresses GitHub MCP vulnerability)
  - PII leakage
- LLM security assessment pipeline works (OpenAI, Azure, Anthropic, local LLMs)
- Addresses real vulnerabilities found in 23% of public MCP servers
- Cross-origin analysis for context hijacking detection

### ✅ CLI Interface
- Well-structured with comprehensive help
- Multiple output formats (JSON, table, markdown, raw)
- Configuration management system with environment variable support
- Auth header support for secured MCP endpoints

### ✅ Proxy Module (New)
- Appears well-architected with proper separation of concerns
- Javelin Guardrails integration for security
- Comprehensive validation service
- Binary: `ramparts-mcp-proxy-stdio`

### ✅ Deploy Docker Image
- Successfully built on GitHub Actions
- Available at: `ghcr.io/shadnygren/ramparts-server:shadnygren-github-actions`
- Runs HTTP server on port 8080

## Recommendations

### Immediate Actions (GitHub Actions Branch)

1. **Docker Build Workflow** ✅ **COMPLETED**
   - Successfully implemented in `.github/workflows/docker-build.yml`
   - Builds Rust binaries first, then Docker images
   - Deploy-Dockerfile builds successfully
   - MCP-Dockerfile fails due to missing common/proxy directories
   - Images pushed to GHCR: `ghcr.io/shadnygren/ramparts-server:shadnygren-github-actions`

2. **Test MCP Server on GitHub Actions**
   - Build with GitHub Actions (modern CPU)
   - Test if MCP server works when built on proper hardware
   - May still fail due to rmcp macro issues

3. **Focus on Scanner and Proxy**
   - These components actually work
   - Ignore MCP server mode until rmcp is fixed/replaced

### Long-term Strategy

1. **Replace rmcp Library**
   - Consider Python rewrite with FastMCP (proven working)
   - Or find alternative Rust MCP implementation
   - Or implement minimal MCP protocol directly

2. **Leverage GitHub Actions**
   - All builds must happen in CI/CD
   - No local Docker builds due to CPU limitations
   - Use workflow artifacts for testing

3. **Consolidate Docker Strategy**
   - Single Dockerfile with build stages
   - Docker Compose for local development
   - Push images to GHCR from workflows

## Test Priority

1. **Test proxy functionality** - New and potentially working
2. **Verify scanner** - Core functionality that works
3. **Skip MCP server testing** - Known broken, not fixable without replacing rmcp

## Project Health Assessment

| Component | Status | Notes |
|-----------|---------|-------|
| Scanner | ✅ Working | Core functionality solid, 79 test functions |
| CLI | ✅ Working | Well-designed interface with 8 subcommands |
| Proxy | 🔄 Unknown | New, needs testing |
| MCP Server | ❌ Broken | rmcp library issues (v0.3.2, v0.6.4 tested) |
| Docker | ⚠️ Problematic | CPU instruction issues (Ivy Bridge limitation) |
| CI/CD | ✅ Good | Comprehensive workflows, multi-architecture builds |
| Documentation | ✅ Good | 3,096 lines of Markdown documentation |
| Test Coverage | ⚠️ Limited | 13 test modules, needs >80% coverage |
| Security Record | ✅ Clean | No CVEs or critical issues identified |

## Next Steps

1. **Create Docker build workflow** in GitHub Actions
2. **Test proxy module** functionality
3. **Document working features** vs broken features clearly
4. **Consider abandoning MCP server** mode until rmcp replacement
5. **Focus on scanner and proxy** as primary value propositions

## Conclusion

Ramparts has evolved into a more comprehensive security tool with the addition of proxy functionality, but the MCP server implementation remains fundamentally broken due to rmcp library issues. The project's value now lies in its scanning capabilities and new proxy features rather than serving as an MCP server itself.

The CPU instruction set incompatibility discovered makes GitHub Actions essential for all build operations. No local builds should be attempted on development machines with older CPUs.

### Business Value Proposition
**EXTREMELY HIGH VALUE** - The security risks in MCP environments are significant and documented:
- **23% of MCP servers contain command injection vulnerabilities**
- Recent critical GitHub MCP prompt injection attacks demonstrate urgent need
- No CVEs or critical issues in Ramparts itself (clean security record)
- First-mover advantage in MCP security scanning space

### Strategic Importance
- **Critical for AI Security**: Addresses real vulnerabilities affecting nearly 1/4 of MCP servers
- **Compliance**: Helps meet emerging AI security framework requirements
- **Risk Mitigation**: Proactive detection before exploitation

---

**Recommendation**: Pivot to positioning Ramparts as a security scanner and proxy tool, deprecating the broken MCP server functionality until a proper MCP library replacement is found. Consider Python rewrite using FastMCP for MCP server functionality while maintaining Rust scanner for performance.