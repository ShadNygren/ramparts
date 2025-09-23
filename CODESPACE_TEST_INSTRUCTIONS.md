# Testing Ramparts in Codespace (No Docker Needed!)

## Step 1: In Your Codespace Terminal

Run these commands in the Codespace terminal (NOT on your laptop):

```bash
# Make the setup script executable
chmod +x codespace_setup.sh

# Run the setup (installs Rust, builds Ramparts, starts server)
./codespace_setup.sh
```

This will:
1. Install Rust in the Codespace (modern CPU with AVX2 support!)
2. Build Ramparts from source
3. Start the HTTP server on port 8080

## Step 2: Get Your Codespace URL

1. In VS Code (in browser), look at the bottom panel
2. Click on the "PORTS" tab
3. Find port 8080 in the list
4. Click the globe icon or copy the forwarded address
5. It will look like: `https://symmetrical-fishstick-xxx-8080.app.github.dev`

## Step 3: Test from Your Laptop

On your Ivy Bridge laptop (no Rust needed!), run:

```bash
# Make sure you have Python and requests
pip3 install requests

# Run the test script
python3 test_codespace_ramparts.py
```

When prompted, paste the Codespace URL from Step 2.

## What This Tests

✅ **Ramparts builds and runs on modern CPUs** (Codespace has AVX2)
✅ **HTTP API server works** (Deploy-Dockerfile functionality)
✅ **Scanner can analyze URLs** (core functionality)
✅ **No SIGILL errors** (CPU compatibility verified)

## Alternative: Test CLI in Codespace

If you want to test the CLI directly in Codespace:

```bash
# In Codespace terminal (after building)
./target/release/ramparts --version
./target/release/ramparts scan https://httpbin.org/json --format json
./target/release/ramparts scan https://example.com --format table
```

## Troubleshooting

- **Port not accessible?** Make sure port visibility is set to "Public" in the Ports tab
- **Connection refused?** Ensure the server is still running in Codespace
- **Codespace stopped?** It auto-stops after 30 min of inactivity - restart it

## Success Criteria

If the tests pass, we've proven:
1. ✅ Ramparts works on modern hardware (no Ivy Bridge limitations)
2. ✅ The HTTP server mode works (what Deploy-Dockerfile provides)
3. ✅ The scanner functionality is operational
4. ✅ No need for Docker to test functionality