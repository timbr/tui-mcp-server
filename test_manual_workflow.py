#!/usr/bin/env python3
import asyncio
import aiohttp
import time
from pathlib import Path

BASE_URL = "http://localhost:8000"

async def main():
    print("Manual Workflow Test")
    print("=" * 50)
    
    # Run a command
    print("\n1. Running 'ls -la' command...")
    async with aiohttp.ClientSession() as session:
        payload = {"command": "ls -la\n"}
        async with session.post(f"{BASE_URL}/mcp/run", json=payload) as resp:
            print(f"   Response: {resp.status}")
    
    # Wait longer for output
    print("\n2. Waiting 5 seconds for output to be sent to browser...")
    await asyncio.sleep(5)
    
    # Take screenshot
    print("\n3. Taking screenshot...")
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/mcp/screenshot") as resp:
            if resp.status == 200:
                data = await resp.read()
                if data[:4] == b'\x89PNG':
                    screenshot_path = Path("test_manual_workflow_screenshot.png")
                    screenshot_path.write_bytes(data)
                    print(f"   Screenshot saved: {screenshot_path.absolute()}")
                else:
                    print("   Invalid PNG data")
            else:
                print(f"   Failed: {resp.status}")

asyncio.run(main())
