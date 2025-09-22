# RAMPARTS FIX PLAN: Resolving rmcp Tool Registration Issue

Last Updated: 2025-09-21

## Executive Summary

The Ramparts MCP server has 5 properly implemented tools that are not being exposed via the MCP protocol. Despite correct macro usage and ServerInfo configuration, the tools array remains empty in the initialize response. This plan outlines a systematic approach to resolve this critical issue.

## Problem Analysis

### Current State
- **Tools Implemented**: 5 tools decorated with `#[tool]` macro
- **ServerHandler**: Properly decorated with `#[tool_handler]`
- **Tool Router**: Using `#[tool_router]` macro on impl block
- **ServerInfo**: Correctly configured with `enable_tools()` capability
- **Result**: Tools array returns empty `[]` in MCP responses

### Root Cause Hypothesis
The rmcp v0.3.2 macro system appears to have a bug or undocumented requirement for tool registration. The `#[tool_router]` macro generates the `tool_router()` function but tools aren't being registered in the protocol layer.

## Solution Strategy

### Phase 1: Version and Dependency Analysis
**Timeline**: 30 minutes
**Priority**: HIGH

1. **Check rmcp Version Compatibility**
   - Current: rmcp v0.3.2
   - Check latest version on crates.io
   - Review changelog for tool registration fixes
   - Check for breaking changes between versions

2. **Analyze Dependency Tree**
   ```bash
   cargo tree -p rmcp
   cargo tree -i rmcp
   ```
   - Identify any version conflicts
   - Check for duplicate dependencies

### Phase 2: Try Alternative Macro Approach
**Timeline**: 1-2 hours
**Priority**: CRITICAL

1. **Switch from tool_router to tool_box**
   ```rust
   // Current approach (not working)
   #[tool_router]
   impl RampartsMcpServer {
       // ...
   }

   // Alternative approach to try
   #[tool_box]
   impl RampartsMcpServer {
       // ...
   }
   ```

2. **Update Initialization**
   ```rust
   pub fn new() -> Self {
       let core = MCPScannerCore::new().expect("core init");
       Self {
           tool_box: Self::tool_box(),  // Changed from tool_router
           counter: Arc::new(Mutex::new(0)),
           core: Arc::new(core),
       }
   }
   ```

3. **Verify Field Name**
   - Change struct field from `tool_router` to `tool_box`
   - Ensure consistency throughout implementation

### Phase 3: Update rmcp Library
**Timeline**: 1 hour
**Priority**: HIGH

1. **Update Cargo.toml**
   ```toml
   [dependencies]
   # Try latest version
   rmcp = "0.3.3"  # or whatever latest is

   # OR try alternative implementation
   # rmcp = { git = "https://github.com/modelcontextprotocol/rust-sdk" }
   ```

2. **Address Breaking Changes**
   - Review migration guide if available
   - Update code to match new API requirements

3. **Clean Build**
   ```bash
   cargo clean
   cargo build --release
   docker build --no-cache -t ramparts:latest-rmcp .
   ```

### Phase 4: Manual Tool Registration Bypass
**Timeline**: 2-3 hours
**Priority**: MEDIUM (if macros still fail)

1. **Implement Custom Tool Registry**
   ```rust
   impl RampartsMcpServer {
       fn register_tools_manually() -> Vec<ToolInfo> {
           vec![
               ToolInfo {
                   name: "health".to_string(),
                   description: "Healthcheck for the Ramparts MCP server".to_string(),
                   parameters: json_schema_for!(EmptyParams),
               },
               // ... other tools
           ]
       }
   }
   ```

2. **Override Tool Listing**
   - Implement custom `list_tools` method
   - Bypass macro-generated implementation
   - Return manually registered tools

3. **Wire Up Tool Execution**
   - Create custom tool dispatcher
   - Map tool names to actual methods
   - Maintain compatibility with MCP protocol

### Phase 5: Debug Macro Expansion
**Timeline**: 1 hour
**Priority**: MEDIUM

1. **Expand Macros**
   ```bash
   cargo expand --lib > expanded.rs
   cargo expand --bin ramparts > expanded_bin.rs
   ```

2. **Analyze Generated Code**
   - Look for `tool_router()` function generation
   - Check tool registration logic
   - Identify where tools should be collected

3. **Add Debug Logging**
   ```rust
   #[tool_handler]
   impl rmcp::ServerHandler for RampartsMcpServer {
       fn get_info(&self) -> ServerInfo {
           eprintln!("DEBUG: tool_router has {} tools", self.tool_router.tools().len());
           // ... rest of implementation
       }
   }
   ```

### Phase 6: Alternative Implementation Research
**Timeline**: 2 hours
**Priority**: LOW (last resort)

1. **Study Working Examples**
   - Clone repositories using rmcp successfully
   - Compare implementation patterns
   - Identify differences in setup

2. **Try Alternative MCP Libraries**
   - modelcontextprotocol/rust-sdk (official)
   - 4t145/rmcp (alternative)
   - Consider implementing minimal MCP protocol directly

### Phase 7: Create Minimal Reproduction
**Timeline**: 1 hour
**Priority**: HIGH (if issue persists)

1. **Create New Project**
   ```bash
   cargo new --lib rmcp-tool-bug
   cd rmcp-tool-bug
   ```

2. **Minimal Implementation**
   - Single tool with minimal dependencies
   - Basic ServerHandler implementation
   - Simple stdio transport

3. **Document Issue**
   - Create detailed bug report
   - Include reproduction steps
   - File issue on rmcp repository

## Testing Strategy

### Test After Each Phase
1. **Build Docker Image**
   ```bash
   docker build --no-cache -t ramparts:test-phase-X .
   ```

2. **Run Test Suite**
   ```bash
   cd test_harness
   python3 test_docker_tools.py ramparts:test-phase-X
   ```

3. **Verify Tool Exposure**
   - Check initialize response for tools capability
   - Verify tools/list returns actual tools
   - Test tool execution

### Success Criteria
- [ ] Initialize response shows `"tools": {}` capability
- [ ] tools/list returns array with 5 tools
- [ ] Each tool has name, description, and parameters
- [ ] Tools can be successfully invoked
- [ ] All test harness tests pass

## Rollback Plan

If all approaches fail:
1. **Fork rmcp Library**
   - Create custom fork with fixes
   - Maintain until upstream is fixed

2. **Implement HTTP REST Wrapper**
   - Expose tools via REST API
   - Create MCP-to-REST bridge
   - Document alternative usage

3. **Switch to Different Protocol**
   - Consider gRPC or GraphQL
   - Maintain MCP compatibility layer
   - Document migration path

## Timeline

**Total Estimated Time**: 8-12 hours

1. **Immediate** (0-2 hours):
   - Phase 1: Version analysis
   - Phase 2: Try tool_box macro

2. **Short-term** (2-4 hours):
   - Phase 3: Update rmcp
   - Phase 5: Debug macro expansion

3. **Medium-term** (4-8 hours):
   - Phase 4: Manual registration (if needed)
   - Phase 7: Minimal reproduction

4. **Long-term** (8+ hours):
   - Phase 6: Alternative implementations
   - Rollback plan execution (if needed)

## Risk Assessment

### High Risk
- Breaking changes in rmcp updates
- Incompatibility with current Rust version
- Fundamental bug in rmcp macro system

### Medium Risk
- Performance impact of manual registration
- Maintenance burden of custom implementation
- Docker build time increases

### Low Risk
- Simple configuration issue
- Missing dependency
- Documentation error

## Documentation Updates

After resolution:
1. Update RAMPARTS_FIXES.md with solution
2. Update CLAUDE.md with lessons learned
3. Create TROUBLESHOOTING.md for future reference
4. Update README.md with any new requirements

## Success Metrics

- Tools exposed: 5/5
- Test suite pass rate: 100%
- Docker image size: < 100MB
- Build time: < 10 minutes
- No runtime performance regression

## Next Immediate Actions

1. ✅ Create this plan document
2. Check current rmcp version vs latest
3. Try tool_box macro approach
4. Test with Docker build
5. Document results

---

## Command Reference

### Quick Test Commands
```bash
# Test current implementation
docker run -i --rm ramparts:latest <<EOF
{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}},"id":1}
{"jsonrpc":"2.0","method":"initialized","params":{}}
{"jsonrpc":"2.0","method":"tools/list","params":{},"id":2}
EOF

# Test with Python harness
cd test_harness
python3 test_docker_tools.py ramparts:latest

# Check macro expansion
cargo expand --lib | grep -A 20 "tool_router"
```

### Docker Build Commands
```bash
# Standard build
docker build -t ramparts:test .

# CPU-restricted build
docker build -f Dockerfile.AVX_only -t ramparts:test .

# No cache build
docker build --no-cache -t ramparts:test .
```

---

**Document Version**: 1.0.0
**Author**: Claude (AI Assistant)
**Status**: ACTIVE PLAN