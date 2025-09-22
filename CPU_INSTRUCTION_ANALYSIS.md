# CPU Instruction Set Analysis: Root Cause Investigation

**Date**: 2025-09-22
**Critical Finding**: Potential CPU instruction incompatibility causing rmcp failures

## 🚨 THE SMOKING GUN

Your observation about CPU instruction sets may have identified the **actual root cause** of rmcp's failures!

## CPU Analysis

### Your CPU: Intel Core i5-3210M (Ivy Bridge, 2012)
- **Architecture**: Ivy Bridge (3rd gen Intel Core)
- **Instruction Sets**:
  - ✅ AVX (Advanced Vector Extensions)
  - ❌ AVX2 (NOT SUPPORTED - introduced in Haswell, 4th gen)
  - ✅ SSE4.1, SSE4.2
  - ✅ AES-NI

### The Critical Issue

When Rust compiles dependencies from crates.io, it uses **TWO different compilation contexts**:

1. **Your code (ramparts)**: Compiled with `RUSTFLAGS="-C target-cpu=ivybridge"`
2. **Dependencies (rmcp, yara-x, etc.)**: May be using **pre-compiled artifacts** or compiled with **default target features**

## 🔍 Evidence Found

### 1. AVX Instructions in Binary
```bash
$ objdump -d ramparts | grep vpshufb
# Found: vpshufb instructions (AVX, not AVX2)
```

The `vpshufb` instruction is AVX (supported), but this proves vector instructions are being used.

### 2. How Cargo Handles Dependencies

**Critical Insight**: Cargo caches compiled dependencies, and these cached artifacts may have been compiled with different CPU targets!

- Dependencies downloaded from crates.io are compiled locally
- BUT: They may use default target features if RUSTFLAGS wasn't set consistently
- Cached artifacts in `~/.cargo/registry/cache/` might have AVX2 instructions

### 3. The Silent Failure Pattern

This explains the bizarre behavior:
- Binary runs (`--version` works) ✅
- Basic code executes ✅
- But rmcp's internal code silently fails ❌
- No error messages (SIGILL is caught/suppressed) ❌

## 🧪 Testing the Hypothesis

### Test 1: Clean Build with Consistent Flags
```bash
# Clear ALL caches
rm -rf target/
rm -rf ~/.cargo/registry/cache/
rm -rf ~/.cargo/registry/index/

# Set RUSTFLAGS globally
export RUSTFLAGS="-C target-cpu=ivybridge"

# Clean build EVERYTHING from source
cargo clean
cargo build --release
```

### Test 2: Check for Illegal Instructions
```bash
# Run with instruction tracing
gdb ./target/release/ramparts
(gdb) catch signal SIGILL
(gdb) run mcp-stdio
# See if it catches illegal instruction
```

### Test 3: Strace for SIGILL
```bash
strace -e signal=all ./target/release/ramparts mcp-stdio 2>&1 | grep -E "SIGILL|Illegal"
```

## 🎯 Why This Makes Perfect Sense

### The rmcp Library Problem

1. **rmcp uses async runtime features** that might leverage SIMD optimizations
2. **tokio and other async libraries** often use CPU-specific optimizations
3. **The library might have inline assembly** or compiler intrinsics assuming AVX2

### Why It Fails Silently

1. **Signal handlers**: Rust runtime might catch SIGILL and suppress it
2. **Async context**: Illegal instruction in async task = task silently dies
3. **No panic propagation**: The error happens at a low level, never bubbles up

## 🔧 The Real Fix

### Option 1: Force Complete Recompilation
```dockerfile
# In Dockerfile
ENV RUSTFLAGS="-C target-cpu=ivybridge"
ENV CARGO_TARGET_DIR="/tmp/target"  # Use fresh target directory

# Force dependencies to rebuild
RUN cargo clean && \
    rm -rf ~/.cargo/registry/cache/ && \
    cargo build --release
```

### Option 2: Use Older Rust Toolchain
```bash
# Use Rust version from when Ivy Bridge was common
rustup default 1.70.0  # Mid-2023 version
cargo build --release
```

### Option 3: Explicit Feature Disabling
```toml
# In Cargo.toml
[profile.release]
opt-level = 2  # Not 3 (less aggressive optimization)
codegen-units = 1
panic = "abort"

# Disable SIMD features in dependencies
[build]
rustflags = ["-C", "target-cpu=ivybridge", "-C", "target-feature=-avx2"]
```

## 📊 Supporting Evidence

### Why Docker Images Still Failed

Even our Docker builds with `RUSTFLAGS="-C target-cpu=ivybridge"` failed because:

1. **Build cache**: Docker might cache layers with wrong instruction sets
2. **Dependency compilation**: Dependencies compiled separately without flags
3. **Multi-stage builds**: Flags not propagated between stages

### The Pattern Matches

- ✅ Binary runs (main() has compatible instructions)
- ✅ --version works (simple code path)
- ❌ MCP stdio fails (rmcp's async runtime hits illegal instruction)
- ❌ No output (SIGILL kills thread before any prints)

## 🚀 Immediate Action Items

1. **Clean build with global RUSTFLAGS**
2. **Test with GDB to catch SIGILL**
3. **Try building on GitHub Actions** (modern CPU) and run locally to confirm it's CPU-related

## 💡 The Irony

We've been debugging the rmcp library's code, but the problem might be at the **instruction level** - the compiled binary contains CPU instructions your processor literally cannot execute!

This would explain EVERYTHING:
- Why it fails silently (illegal instruction)
- Why Docker doesn't help (still wrong instructions)
- Why no error messages (crash before logging)
- Why manual registration doesn't work (never reaches our code)

## Conclusion

**This is likely the root cause!** The rmcp library (or its dependencies) are being compiled with AVX2 instructions that your Ivy Bridge CPU cannot execute. The solution is ensuring ALL code, including dependencies, is compiled with the `ivybridge` target.

The Python rewrite would sidestep this entirely since Python handles CPU compatibility at a higher level.