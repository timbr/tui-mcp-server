import asyncio
import os
import tempfile
from pathlib import Path
from typing import Optional
from playwright.async_api import async_playwright, Browser, Page


class BrowserManager:
    """Manages the headless browser instance for screenshots."""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self.screenshot_dir = tempfile.mkdtemp(prefix="tui_mcp_")
    
    async def start(self):
        """Start the headless browser and navigate to the terminal page."""
        try:
            self.playwright = await async_playwright().start()
            
            # Launch the browser
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                ]
            )
            
            # Create a new page
            self.page = await self.browser.new_page(
                viewport={"width": 1024, "height": 768}
            )
            
            # Navigate to the local server
            # We'll wait a bit for the server to be ready
            await asyncio.sleep(1)
            
            try:
                await self.page.goto("http://localhost:8000/", wait_until="networkidle")
            except Exception as e:
                print(f"Warning: Could not navigate immediately: {e}")
                # The page might still load, we'll try again on first screenshot
            
            print("Browser started successfully")
        except Exception as e:
            print(f"Error starting browser: {e}")
            raise
    
    async def stop(self):
        """Stop the browser and clean up."""
        if self.page:
            try:
                await self.page.close()
            except Exception as e:
                print(f"Error closing page: {e}")
        
        if self.browser:
            try:
                await self.browser.close()
            except Exception as e:
                print(f"Error closing browser: {e}")
        
        if self.playwright:
            try:
                await self.playwright.stop()
            except Exception as e:
                print(f"Error stopping playwright: {e}")
        
        print("Browser stopped")
    
    async def take_screenshot(self) -> Optional[str]:
        """Take a screenshot of the terminal."""
        if not self.page:
            print("Page not initialized")
            return None
        
        try:
            # Ensure we're on the right page
            if self.page.url != "http://localhost:8000/":
                try:
                    await self.page.goto("http://localhost:8000/", wait_until="networkidle", timeout=5000)
                except Exception as e:
                    print(f"Warning: Could not navigate to page: {e}")
            
            # Wait for the xterm screen element to be present and have content
            try:
                await self.page.wait_for_selector('.xterm-screen', timeout=3000)
                print("Xterm screen element found")
            except Exception as e:
                print(f"Warning: Xterm screen not found: {e}")
            
            # Additional wait for rendering and content
            await asyncio.sleep(2)
            
            # Get the terminal container element
            terminal_element = await self.page.query_selector("#terminal")
            
            if terminal_element:
                # Take a screenshot of just the terminal element
                screenshot_path = os.path.join(self.screenshot_dir, "terminal.png")
                await terminal_element.screenshot(path=screenshot_path)
            else:
                # Fallback: screenshot the entire viewport
                screenshot_path = os.path.join(self.screenshot_dir, "terminal.png")
                await self.page.screenshot(path=screenshot_path)
            
            print(f"Screenshot saved to {screenshot_path}")
            return screenshot_path
        
        except Exception as e:
            print(f"Error taking screenshot: {e}")
            return None
