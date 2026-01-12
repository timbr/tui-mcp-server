#!/usr/bin/env python3
"""
Test script for the TUI MCP Server.
Verifies all endpoints and functionality.
"""

import asyncio
import aiohttp
import json
import time
import sys
from pathlib import Path


BASE_URL = "http://localhost:8000"


async def test_health():
    """Test the health endpoint."""
    print("\n=== Testing Health Endpoint ===")
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/health") as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"✓ Health check passed: {data}")
                return True
            else:
                print(f"✗ Health check failed: {resp.status}")
                return False


async def test_run_command():
    """Test the /mcp/run endpoint."""
    print("\n=== Testing /mcp/run Endpoint ===")
    async with aiohttp.ClientSession() as session:
        payload = {"command": "echo 'Hello from TUI MCP Server'"}
        async with session.post(f"{BASE_URL}/mcp/run", json=payload) as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"✓ Command sent: {data}")
                await asyncio.sleep(1)  # Wait for output
                return True
            else:
                print(f"✗ Command failed: {resp.status}")
                return False


async def test_wait_for_stable_output():
    """Test the /mcp/wait_for_stable_output endpoint."""
    print("\n=== Testing /mcp/wait_for_stable_output Endpoint ===")
    async with aiohttp.ClientSession() as session:
        payload = {"timeout_seconds": 5}
        async with session.post(f"{BASE_URL}/mcp/wait_for_stable_output", json=payload) as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"✓ Output stabilized: {data}")
                return True
            else:
                print(f"✗ Wait failed: {resp.status}")
                return False


async def test_screenshot():
    """Test the /mcp/screenshot endpoint."""
    print("\n=== Testing /mcp/screenshot Endpoint ===")
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/mcp/screenshot") as resp:
            if resp.status == 200:
                data = await resp.read()
                # Check if it's a valid PNG (PNG signature: 89 50 4E 47)
                if data[:4] == b'\x89PNG':
                    screenshot_path = Path("test_screenshot.png")
                    screenshot_path.write_bytes(data)
                    print(f"✓ Screenshot captured: {len(data)} bytes")
                    print(f"  Saved to: {screenshot_path.absolute()}")
                    return True
                else:
                    print(f"✗ Invalid PNG data received")
                    return False
            else:
                print(f"✗ Screenshot failed: {resp.status}")
                return False


async def test_send_keys():
    """Test the /mcp/send_keys endpoint."""
    print("\n=== Testing /mcp/send_keys Endpoint ===")
    async with aiohttp.ClientSession() as session:
        # Send a simple command via send_keys
        payload = {"keys": "echo 'Keys sent successfully'\n"}
        async with session.post(f"{BASE_URL}/mcp/send_keys", json=payload) as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"✓ Keys sent: {data}")
                await asyncio.sleep(1)  # Wait for output
                return True
            else:
                print(f"✗ Send keys failed: {resp.status}")
                return False


async def test_interactive_workflow():
    """Test a complete interactive workflow."""
    print("\n=== Testing Complete Interactive Workflow ===")
    
    try:
        # 1. Run a command
        print("\n1. Running command: 'ls -la'")
        async with aiohttp.ClientSession() as session:
            payload = {"command": "ls -la"}
            async with session.post(f"{BASE_URL}/mcp/run", json=payload) as resp:
                if resp.status != 200:
                    print("✗ Failed to run command")
                    return False
        
        # 2. Wait for output
        print("2. Waiting for output to stabilize...")
        async with aiohttp.ClientSession() as session:
            payload = {"timeout_seconds": 5}
            async with session.post(f"{BASE_URL}/mcp/wait_for_stable_output", json=payload) as resp:
                if resp.status != 200:
                    print("✗ Failed to wait for stable output")
                    return False
        
        # 3. Take screenshot
        print("3. Taking screenshot...")
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/mcp/screenshot") as resp:
                if resp.status != 200:
                    print("✗ Failed to take screenshot")
                    return False
                data = await resp.read()
                if data[:4] != b'\x89PNG':
                    print("✗ Invalid PNG data")
                    return False
                screenshot_path = Path("test_workflow_screenshot.png")
                screenshot_path.write_bytes(data)
                print(f"✓ Screenshot saved to: {screenshot_path.absolute()}")
        
        print("\n✓ Complete workflow test passed!")
        return True
    
    except Exception as e:
        print(f"✗ Workflow test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("=" * 50)
    print("TUI MCP Server Test Suite")
    print("=" * 50)
    
    # Check if server is running
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/health", timeout=aiohttp.ClientTimeout(total=2)) as resp:
                pass
    except Exception as e:
        print(f"\n✗ Server is not running at {BASE_URL}")
        print(f"  Error: {e}")
        print(f"\n  Start the server with:")
        print(f"  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
        sys.exit(1)
    
    # Run tests
    results = []
    
    results.append(("Health Check", await test_health()))
    results.append(("Run Command", await test_run_command()))
    results.append(("Wait for Stable Output", await test_wait_for_stable_output()))
    results.append(("Send Keys", await test_send_keys()))
    results.append(("Screenshot", await test_screenshot()))
    results.append(("Complete Workflow", await test_interactive_workflow()))
    
    # Print summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed!")
        sys.exit(0)
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
