#!/usr/bin/env python3
"""
Test Ramparts running in GitHub Codespace from local laptop.
Run this AFTER starting the server in Codespace.
"""

import requests
import json
import sys
from time import sleep

# GitHub Codespace forwards ports automatically
# Check the "Ports" tab in VS Code to get the URL
CODESPACE_URL = input("Enter your Codespace forwarded URL (e.g., https://xxx-8080.app.github.dev): ").strip()

if not CODESPACE_URL:
    print("❌ No URL provided. In VS Code Codespace:")
    print("1. Click on the 'Ports' tab at the bottom")
    print("2. Find port 8080")
    print("3. Copy the forwarded address")
    sys.exit(1)

# Ensure URL has correct format
if not CODESPACE_URL.startswith("http"):
    CODESPACE_URL = f"https://{CODESPACE_URL}"

print(f"\n🧪 Testing Ramparts at {CODESPACE_URL}")

# Test 1: Health check
try:
    print("\n1️⃣ Testing health endpoint...")
    response = requests.get(f"{CODESPACE_URL}/health", timeout=10)
    if response.status_code == 200:
        print("✅ Health check passed")
    else:
        print(f"⚠️ Health endpoint returned {response.status_code}")
except requests.exceptions.RequestException as e:
    print(f"❌ Health check failed: {e}")

# Test 2: Scan endpoint with httpbin
try:
    print("\n2️⃣ Testing scan endpoint...")
    scan_request = {
        "url": "https://httpbin.org/json",
        "timeout": 30
    }

    response = requests.post(
        f"{CODESPACE_URL}/v1/ramparts/scan",
        json=scan_request,
        headers={"Content-Type": "application/json"},
        timeout=35
    )

    if response.status_code == 200:
        result = response.json()
        print("✅ Scan completed successfully!")
        print(f"   - Status: {result.get('status', 'unknown')}")
        if 'scan_results' in result:
            findings = result['scan_results'].get('findings', [])
            print(f"   - Findings: {len(findings)} items")
            if findings:
                print("   - Sample finding:", findings[0].get('title', 'N/A'))
        print("\n📊 Full response:")
        print(json.dumps(result, indent=2)[:500] + "..." if len(json.dumps(result)) > 500 else json.dumps(result, indent=2))
    else:
        print(f"❌ Scan failed with status {response.status_code}")
        print(f"   Response: {response.text[:200]}")

except requests.exceptions.RequestException as e:
    print(f"❌ Scan request failed: {e}")

# Test 3: Test invalid URL handling
try:
    print("\n3️⃣ Testing error handling with invalid URL...")
    scan_request = {"url": "not-a-valid-url", "timeout": 10}

    response = requests.post(
        f"{CODESPACE_URL}/v1/ramparts/scan",
        json=scan_request,
        headers={"Content-Type": "application/json"},
        timeout=15
    )

    print(f"   - Status code: {response.status_code}")
    if response.status_code >= 400:
        print("✅ Properly rejected invalid URL")
    else:
        print("⚠️ Accepted invalid URL - may need validation")

except requests.exceptions.RequestException as e:
    print(f"❌ Error handling test failed: {e}")

print("\n" + "="*50)
print("🎉 Testing complete!")
print("\n💡 If tests failed, check that:")
print("1. The Ramparts server is running in Codespace")
print("2. Port 8080 is forwarded (check Ports tab)")
print("3. The URL is correct (should be like https://xxx-8080.app.github.dev)")
print("4. You're not behind a restrictive firewall")