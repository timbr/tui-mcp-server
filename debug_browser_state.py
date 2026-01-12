#!/usr/bin/env python3
"""Debug script to check browser state and console logs."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.browser_manager import BrowserManager


async def main():
    """Debug the browser state."""
    print("Starting browser state debug...")
    
    browser_manager = BrowserManager()
    
    try:
        print("\n1. Starting browser...")
        await browser_manager.start()
        print("   ✓ Browser started")
        
        print("\n2. Waiting for page load...")
        await asyncio.sleep(3)
        
        print("\n3. Checking page HTML...")
        html = await browser_manager.page.content()
        print(f"   Page HTML length: {len(html)} bytes")
        print(f"   Contains 'Terminal': {'Terminal' in html}")
        print(f"   Contains 'xterm': {'xterm' in html}")
        print(f"   Contains '/static/lib/xterm.js': {'/static/lib/xterm.js' in html}")
        
        print("\n4. Checking browser console logs...")
        try:
            logs = await browser_manager.page.evaluate("""
                () => {
                    return {
                        hasTerminal: typeof Terminal !== 'undefined',
                        hasFitAddon: typeof FitAddon !== 'undefined',
                        hasWebSocket: typeof WebSocket !== 'undefined',
                        terminalElement: !!document.getElementById('terminal'),
                        xtermElement: !!document.querySelector('.xterm'),
                        xtermScreen: !!document.querySelector('.xterm-screen'),
                    };
                }
            """)
            print(f"   Terminal class available: {logs['hasTerminal']}")
            print(f"   FitAddon class available: {logs['hasFitAddon']}")
            print(f"   WebSocket available: {logs['hasWebSocket']}")
            print(f"   Terminal element exists: {logs['terminalElement']}")
            print(f"   Xterm element exists: {logs['xtermElement']}")
            print(f"   Xterm screen exists: {logs['xtermScreen']}")
        except Exception as e:
            print(f"   Error checking page state: {e}")
        
        print("\n5. Checking for JavaScript errors...")
        try:
            # Set up console message listener
            messages = []
            def on_message(msg):
                messages.append({
                    'type': msg.type,
                    'text': msg.text,
                    'location': msg.location
                })
            
            browser_manager.page.on('console', on_message)
            
            # Trigger a reload to capture console messages
            await browser_manager.page.reload(wait_until='networkidle')
            await asyncio.sleep(2)
            
            if messages:
                print(f"   Found {len(messages)} console messages:")
                for msg in messages[:10]:  # Show first 10
                    print(f"     [{msg['type']}] {msg['text']}")
            else:
                print("   No console messages captured")
        except Exception as e:
            print(f"   Error capturing console: {e}")
        
        print("\n6. Checking page structure...")
        try:
            body_html = await browser_manager.page.evaluate("() => document.body.innerHTML.substring(0, 500)")
            print(f"   Body HTML preview: {body_html}")
        except Exception as e:
            print(f"   Error getting body HTML: {e}")
        
        print("\n7. Checking all script tags...")
        try:
            scripts = await browser_manager.page.evaluate("""
                () => {
                    const scripts = document.querySelectorAll('script');
                    return Array.from(scripts).map(s => ({
                        src: s.src,
                        inline: s.innerHTML.substring(0, 100)
                    }));
                }
            """)
            print(f"   Found {len(scripts)} script tags:")
            for i, script in enumerate(scripts):
                if script['src']:
                    print(f"     {i+1}. External: {script['src']}")
                else:
                    print(f"     {i+1}. Inline: {script['inline'][:50]}...")
        except Exception as e:
            print(f"   Error checking scripts: {e}")
        
        print("\n8. Taking screenshot...")
        screenshot_path = await browser_manager.take_screenshot()
        if screenshot_path:
            print(f"   ✓ Screenshot saved to: {screenshot_path}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\n9. Stopping browser...")
        await browser_manager.stop()
        print("   ✓ Browser stopped")


if __name__ == "__main__":
    asyncio.run(main())
