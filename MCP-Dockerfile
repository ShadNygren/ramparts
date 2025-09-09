FROM rust:1.75-slim AS builder

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
COPY assets ./assets

# Build the application
RUN cargo build --release

FROM ubuntu:24.04

LABEL maintainer="ShadNygren"
LABEL org.opencontainers.image.title="Ramparts MCP Server"
LABEL org.opencontainers.image.description="Ramparts MCP security scanner running as MCP server"
LABEL org.opencontainers.image.source="https://github.com/ShadNygren/ramparts"

# Install runtime dependencies including Docker CLI
RUN apt-get update && apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    yara \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get update \
    && apt-get install -y docker-ce-cli \
    && addgroup --system --gid 1001 ramparts \
    && adduser --system --uid 1001 --gid 1001 ramparts \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy application binary and required files
COPY --from=builder --chown=ramparts:ramparts /app/target/release/ramparts /app/
COPY --from=builder --chown=ramparts:ramparts /app/rules /app/rules

# Set executable permissions
RUN chmod +x /app/ramparts

# Switch to non-root user (except when Docker socket access needed)
USER ramparts

# Environment variable to suppress human-readable output for MCP stdio
ENV RAMPARTS_MCP_STDIO=1

# Default: run as MCP stdio server (MCP Toolkit/hosts connect over stdio)
ENTRYPOINT ["/app/ramparts", "mcp-stdio"]


