FROM rust:latest AS builder

WORKDIR /app

# Install build dependencies including YARA
RUN apt-get update && apt-get install -y \
    pkg-config \
    libssl-dev \
    yara \
    libyara-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first for better layer caching
COPY Cargo.toml Cargo.lock ./
COPY build.rs ./

# Create dummy src directory to cache dependencies
RUN mkdir src && \
    echo "fn main() {}" > src/main.rs && \
    cargo build --release && \
    rm -rf src

# Copy actual source code
COPY src ./src
COPY rules ./rules

# Build the application with verbose output
RUN echo "Starting Rust build at $(date)" && \
    cargo --version && \
    rustc --version && \
    echo "Building release binaries..." && \
    cargo build --release --verbose 2>&1 | tee /tmp/build.log | grep -E "Compiling|Finished|warning:|error:" || true && \
    echo "Build completed at $(date)" && \
    ls -la target/release/ && \
    echo "Ramparts binary size: $(stat -c %s target/release/ramparts 2>/dev/null || echo 'not found')" && \
    echo "Hello binary size: $(stat -c %s target/release/hello 2>/dev/null || echo 'not found')"

FROM ubuntu:24.04

LABEL maintainer="ShadNygren"
LABEL org.opencontainers.image.title="Ramparts MCP Server"
LABEL org.opencontainers.image.description="Ramparts MCP security scanner running as MCP server"
LABEL org.opencontainers.image.source="https://github.com/ShadNygren/ramparts"

# Install runtime dependencies including Docker CLI and debugging tools
RUN apt-get update && apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    yara \
    strace \
    gdb \
    file \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get update \
    && apt-get install -y docker-ce-cli \
    && addgroup --system --gid 1001 ramparts \
    && adduser --system --uid 1001 --gid 1001 ramparts \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy application binaries and required files
COPY --from=builder --chown=ramparts:ramparts /app/target/release/ramparts /app/
# Try to copy hello binary if it exists (will be created if src/bin/hello.rs exists)
COPY --from=builder --chown=ramparts:ramparts /app/target/release/hello* /app/
COPY --from=builder --chown=ramparts:ramparts /app/rules /app/rules

# Set executable permissions and test binaries with debugging
RUN chmod +x /app/ramparts && \
    ls -la /app/ && \
    echo "=== Binary analysis ===" && \
    file /app/ramparts && \
    echo "=== Library dependencies ===" && \
    ldd /app/ramparts || echo "ldd failed" && \
    echo "=== Testing hello binary ===" && \
    if [ -f /app/hello ]; then chmod +x /app/hello && /app/hello || echo "Hello binary failed with code $?"; else echo "No hello binary"; fi && \
    echo "=== Testing ramparts with strace (version) ===" && \
    strace -e trace=write,open,openat /app/ramparts --version 2>&1 | head -20 || echo "Ramparts --version failed with code $?" && \
    echo "=== Testing ramparts binary (help) ===" && \
    /app/ramparts --help 2>&1 | head -5 || echo "Ramparts --help failed with code $?" && \
    echo "=== Testing ramparts binary (unknown arg) ===" && \
    /app/ramparts --unknown-arg 2>&1 || echo "Ramparts unknown arg failed with code $?" && \
    echo "=== Testing ramparts binary directly ===" && \
    timeout 2 /app/ramparts 2>&1 || echo "Direct execution failed/timed out with code $?" && \
    echo "=== Testing with explicit RUST_BACKTRACE ===" && \
    RUST_BACKTRACE=1 /app/ramparts --version 2>&1 || echo "With backtrace failed with code $?"

# Switch to non-root user (except when Docker socket access needed)
USER ramparts

# Environment variable to suppress human-readable output for MCP stdio
ENV RAMPARTS_MCP_STDIO=1

# Default: run as MCP stdio server (MCP Toolkit/hosts connect over stdio)
ENTRYPOINT ["/app/ramparts", "mcp-stdio"]


