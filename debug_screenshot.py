#!/usr/bin/env python3
"""Debug script to test screenshot functionality."""

import asyncio
import os
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from app.browser_manager import BrowserManager


async def main():
    """Test the browser manager and screenshot functionality."""
    print("Starting debug screenshot test...")
    
    browser_manager = BrowserManager()
    
    try:
        print("\n1. Starting browser...")
        await browser_manager.start()
        print("   ✓ Browser started")
        
        print("\n2. Navigating to terminal page...")
        await asyncio.sleep(2)
        
        print("\n3. Taking initial screenshot...")
        screenshot_path = await browser_manager.take_screenshot()
        if screenshot_path:
            print(f"   ✓ Screenshot saved to: {screenshot_path}")
            file_size = os.path.getsize(screenshot_path)
            print(f"   File size: {file_size} bytes")
        else:
            print("   ✗ Failed to take screenshot")
        
        print("\n4. Checking page content...")
        try:
            # Get the terminal element
            terminal = await browser_manager.page.query_selector("#terminal")
            if terminal:
                print("   ✓ Terminal element found")
                
                # Get the text content
                text_content = await terminal.text_content()
                print(f"   Terminal text content: {repr(text_content[:100] if text_content else 'None')}")
            else:
                print("   ✗ Terminal element not found")
        except Exception as e:
            print(f"   ✗ Error checking page: {e}")
        
        print("\n5. Checking Xterm.js screen...")
        try:
            xterm_screen = await browser_manager.page.query_selector(".xterm-screen")
            if xterm_screen:
                print("   ✓ Xterm screen element found")
                text = await xterm_screen.text_content()
                print(f"   Xterm text: {repr(text[:100] if text else 'None')}")
            else:
                print("   ✗ Xterm screen element not found")
        except Exception as e:
            print(f"   ✗ Error checking Xterm: {e}")
        
        print("\n6. Checking WebSocket status...")
        try:
            ws_status = await browser_manager.page.evaluate("() => window.ws ? window.ws.readyState : 'undefined'")
            print(f"   WebSocket readyState: {ws_status}")
        except Exception as e:
            print(f"   ✗ Error checking WebSocket: {e}")
        
        print("\n7. Taking another screenshot after delay...")
        await asyncio.sleep(3)
        screenshot_path = await browser_manager.take_screenshot()
        if screenshot_path:
            print(f"   ✓ Screenshot saved to: {screenshot_path}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\n8. Stopping browser...")
        await browser_manager.stop()
        print("   ✓ Browser stopped")


if __name__ == "__main__":
    asyncio.run(main())
