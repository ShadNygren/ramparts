# Ramparts Review - September 22, 2025

## Executive Summary

This review assesses the current state of Ramparts after pulling the latest updates from upstream (12 new commits since September 11). The project has evolved significantly with the addition of proxy functionality and Javelin Guardrails integration, but fundamental issues with the MCP server implementation remain unresolved.

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

4. **New CLI Command**
   - Added `Proxy` command for starting MCP proxy server

## GitHub Actions Workflows

The repository has comprehensive CI/CD workflows:

1. **`cicd.yml`** - Main CI/CD pipeline
2. **`cron.yml`** - Scheduled builds (changed from Friday to Monday)
3. **`e2e.yml`** - End-to-end testing
4. **`pr-check.yml`** - Pull request validation (11KB - very comprehensive)
5. **`release.yml`** - Release builds for multiple platforms (Ubuntu, Windows, macOS)

### Key Observations

- Workflows build for **multiple architectures**: x86_64 on Ubuntu 24.04, Windows 2022, macOS 15
- Uses **modern GitHub Actions** with proper caching
- Includes artifact uploads and cross-platform testing
- **No Docker image builds in workflows** - still using local Docker approach

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
- YARA rule integration functional
- LLM security assessment pipeline works

### ✅ CLI Interface
- Well-structured with comprehensive help
- Multiple output formats (JSON, table, markdown)
- Configuration management system

### ✅ Proxy Module (New)
- Appears well-architected with proper separation of concerns
- Javelin Guardrails integration for security
- Comprehensive validation service

## Recommendations

### Immediate Actions (GitHub Actions Branch)

1. **Add Docker Build Workflow**
   ```yaml
   # .github/workflows/docker-build.yml
   name: Docker Build
   on:
     push:
       branches: [main, shadnygren/github-actions]
   jobs:
     build:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - name: Build Docker images
           run: |
             docker build -f MCP-Dockerfile -t ramparts-mcp:latest .
             docker build -f Deploy-Dockerfile -t ramparts-server:latest .
   ```

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
| Scanner | ✅ Working | Core functionality solid |
| CLI | ✅ Working | Well-designed interface |
| Proxy | 🔄 Unknown | New, needs testing |
| MCP Server | ❌ Broken | rmcp library issues |
| Docker | ⚠️ Problematic | CPU instruction issues |
| CI/CD | ✅ Good | Comprehensive workflows |
| Documentation | ✅ Good | Well-documented |

## Next Steps

1. **Create Docker build workflow** in GitHub Actions
2. **Test proxy module** functionality
3. **Document working features** vs broken features clearly
4. **Consider abandoning MCP server** mode until rmcp replacement
5. **Focus on scanner and proxy** as primary value propositions

## Conclusion

Ramparts has evolved into a more comprehensive security tool with the addition of proxy functionality, but the MCP server implementation remains fundamentally broken due to rmcp library issues. The project's value now lies in its scanning capabilities and new proxy features rather than serving as an MCP server itself.

The CPU instruction set incompatibility discovered makes GitHub Actions essential for all build operations. No local builds should be attempted on development machines with older CPUs.

---

**Recommendation**: Pivot to positioning Ramparts as a security scanner and proxy tool, deprecating the broken MCP server functionality until a proper MCP library replacement is found.