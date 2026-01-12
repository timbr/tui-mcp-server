#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.browser_manager import BrowserManager

async def main():
    browser_manager = BrowserManager()
    
    try:
        print("Starting browser...")
        await browser_manager.start()
        
        print("\nWaiting for page to load...")
        await asyncio.sleep(3)
        
        print("\nChecking terminal element visibility...")
        result = await browser_manager.page.evaluate("""
            () => {
                const terminal = document.getElementById('terminal');
                const xterm = document.querySelector('.xterm');
                const screen = document.querySelector('.xterm-screen');
                
                return {
                    terminalExists: !!terminal,
                    terminalDisplay: terminal ? window.getComputedStyle(terminal).display : 'N/A',
                    terminalVisibility: terminal ? window.getComputedStyle(terminal).visibility : 'N/A',
                    xtermExists: !!xterm,
                    xtermDisplay: xterm ? window.getComputedStyle(xterm).display : 'N/A',
                    xtermVisibility: xterm ? window.getComputedStyle(xterm).visibility : 'N/A',
                    screenExists: !!screen,
                    screenDisplay: screen ? window.getComputedStyle(screen).display : 'N/A',
                    screenHTML: screen ? screen.innerHTML.substring(0, 200) : 'N/A',
                    screenText: screen ? screen.textContent.substring(0, 100) : 'N/A',
                    bodyBG: window.getComputedStyle(document.body).backgroundColor,
                    xtermBG: xterm ? window.getComputedStyle(xterm).backgroundColor : 'N/A',
                    xtermColor: xterm ? window.getComputedStyle(xterm).color : 'N/A',
                };
            }
        """)
        
        print("\nElement Visibility:")
        for key, value in result.items():
            print(f"  {key}: {value}")
        
        print("\nTaking screenshot...")
        screenshot = await browser_manager.take_screenshot()
        print(f"Screenshot saved: {screenshot}")
        
    finally:
        await browser_manager.stop()

asyncio.run(main())
