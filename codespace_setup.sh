#!/bin/bash
set -euo pipefail

echo "==============================================="
echo "🚀 Setting up Ramparts in Codespace"
echo "==============================================="

# Install Rust if not already installed
if ! command -v cargo &> /dev/null; then
    echo "📦 Installing Rust..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source $HOME/.cargo/env
else
    echo "✅ Rust already installed"
    source $HOME/.cargo/env
fi

# Install build dependencies
echo "📦 Installing build dependencies..."
sudo apt-get update
sudo apt-get install -y pkg-config libssl-dev

# Build Ramparts
echo "🔨 Building Ramparts..."
cargo build --release --all-features

# Test the binary
echo "🧪 Testing binary..."
./target/release/ramparts --version

# Start HTTP server on port 8080
echo "🚀 Starting Ramparts HTTP server on port 8080..."
echo "The server will be accessible from your laptop via the forwarded port"
./target/release/ramparts server --port 8080