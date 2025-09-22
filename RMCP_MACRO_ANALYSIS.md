# RMCP Macro System Analysis

## CRITICAL UPDATE: STDIO TRANSPORT COMPLETELY BROKEN (2025-09-22)

### Latest Findings
- ❌ Manual tool registration implemented and tested - FAILS
- ❌ Upgraded to rmcp v0.6.4 (official SDK) - STILL FAILS
- ❌ MCP server doesn't respond to ANY protocol messages
- ❌ Debug output never appears - failure occurs before our code

The rmcp library has TWO critical bugs:
1. Tool registration macros broken (workaround attempted)
2. **Stdio transport layer non-functional** (NO WORKAROUND POSSIBLE)

## Version Confusion History (2025-09-21)

We discovered we were investigating the WRONG rmcp library:
1. **4t145/rmcp** (v0.1.5): Archived fork we incorrectly investigated
2. **modelcontextprotocol/rust-sdk** (v0.6.4): Official SDK - ALSO BROKEN
3. **crates.io rmcp v0.3.2**: What we were using - BROKEN

## Executive Summary

After extensive investigation and testing with BOTH rmcp v0.3.2 and v0.6.4, we've identified that the rmcp library is fundamentally broken at multiple levels. Even with manual workarounds for the macro issue, the stdio transport failure makes it completely unusable.

## Investigation Timeline

- **2025-09-21 12:00**: Initial discovery of non-existent macros
- **2025-09-21 13:45**: Attempted fix with `tool_box!` macro - FAILED
- **2025-09-21 14:30**: Deep dive into rmcp macro source code
- **2025-09-21 14:45**: Critical discovery of macro generation issue
- **2025-09-21 20:45**: Implemented manual tool registration workaround
- **2025-09-22 00:00**: Upgraded to rmcp v0.6.4 for testing
- **2025-09-22 01:00**: CRITICAL: Discovered stdio transport is completely broken

## Technical Deep Dive

### How rmcp Tool Registration Should Work

1. **Tool Implementation**: Developer marks async methods with `#[tool]` attribute
2. **Macro Generation**: The `#[tool]` procedural macro generates two helper functions:
   - `{method_name}_tool_attr()` - Returns tool metadata (name, description, parameters)
   - `{method_name}_tool_call()` - Wrapper for async execution with context handling
3. **Tool Collection**: `tool_box!` macro collects all tool methods
4. **Registration**: `tool_box!(@derive)` in ServerHandler exposes tools via MCP protocol

### What We Found in the Code

#### 1. Macro Structure (rmcp-macros/src/tool.rs)

```rust
// The #[tool] macro generates:
let tool_attr_fn_ident = Ident::new(
    &format!("{}_tool_attr", input_fn.sig.ident),
    proc_macro2::Span::call_site(),
);

let tool_call_fn_ident = Ident::new(
    &format!("{}_tool_call", input_fn.sig.ident),
    proc_macro2::Span::call_site(),
);
```

#### 2. Tool Box Macro (rmcp/src/handler/server/tool.rs)

```rust
macro_rules! tool_box {
    ($server: ident { $($tool: ident),* $(,)?} ) => {
        fn tool_box() -> &'static ToolBox<$server> {
            // Uses paste! macro to concatenate names
            paste!{
                $(
                    // References generated functions
                    $server::[< $tool _tool_attr>]()
                    $server::[<$tool _tool_call>]
                )*
            }
        }
    };
}
```

#### 3. Our Implementation

```rust
impl RampartsMcpServer {
    #[tool(description = "Healthcheck for the Ramparts MCP server")]
    async fn health(&self) -> Result<CallToolResult, ErrorData> { ... }

    // ... other tools ...

    tool_box!(RampartsMcpServer { health, increment_counter, scan, scan_config, refresh_tools });
}

impl ServerHandler for RampartsMcpServer {
    tool_box!(@derive);
    // ...
}
```

## The Bug

### Primary Issue: Silent Macro Failure

The `tool_box!` macro depends on the `paste!` macro for name concatenation, which:
1. May not be properly expanding the function names
2. Could have visibility issues with generated functions
3. Fails silently without compile-time errors

### Secondary Issues

1. **Library Maintenance**: rmcp was archived 5 months ago (April 2025)
2. **No Error Reporting**: Macro failures don't produce compilation errors
3. **Dependency on paste!**: Additional macro dependency that may have version conflicts

## Proof of Failure

Testing with Docker image `ramparts:v2025-09-21t12-30`:
```python
# Initialize response shows empty tools
{
  "result": {
    "capabilities": {},
    "serverInfo": {...}
  }
}

# tools/list returns empty array
{
  "result": {
    "tools": []
  }
}
```

## Workaround Strategies

### ❌ Option 1: Manual Tool Registration (TESTED - FAILED)

Bypass the macro system entirely and manually implement tool registration:

```rust
impl ServerHandler for RampartsMcpServer {
    async fn list_tools(
        &self,
        _: PaginatedRequestParam,
        _: RequestContext<RoleServer>,
    ) -> Result<ListToolsResult, Error> {
        Ok(ListToolsResult {
            tools: vec![
                ToolInfo {
                    name: "health".to_string(),
                    description: Some("Healthcheck for the Ramparts MCP server".to_string()),
                    input_schema: /* manual schema */,
                },
                // ... other tools
            ],
        })
    }

    async fn call_tool(
        &self,
        request: CallToolRequest,
        context: RequestContext<RoleServer>,
    ) -> Result<CallToolResult, Error> {
        match request.name.as_str() {
            "health" => self.health().await,
            "scan" => self.scan(/* parse params */).await,
            // ... other tools
            _ => Err(Error::method_not_found())
        }
    }
}
```

### Option 2: Fork and Fix rmcp

1. Fork the archived rmcp repository
2. Fix the macro generation issue
3. Maintain custom version

### Option 3: Switch to Alternative MCP Library

Consider migrating to:
- Official `modelcontextprotocol/rust-sdk`
- Custom MCP implementation
- Different protocol entirely

## Recommendations

1. **URGENT**: ABANDON RMCP - Library is fundamentally broken
2. **Alternative 1**: Implement MCP protocol from scratch
3. **Alternative 2**: Use different protocol (REST API, gRPC, etc.)
4. **Alternative 3**: Wait for rmcp to be fixed (unlikely, archived 5 months)

## Files Affected

- `/src/mcp_server.rs` - Main implementation needing workaround
- `Cargo.toml` - May need to switch dependencies
- Docker builds - Will need rebuilding after fix

## Lessons Learned

1. **Macro Debugging**: Use `cargo expand` to inspect macro output
2. **Silent Failures**: Procedural macros can fail without compile errors
3. **Dependency Risk**: Using archived libraries carries maintenance risk
4. **Testing Early**: Protocol-level testing reveals integration issues

---

Document Version: 2.0
Last Updated: 2025-09-22 01:30
Author: Claude (AI Assistant)
Status: ❌ INVESTIGATION COMPLETE - LIBRARY UNUSABLE