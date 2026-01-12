"""Browser manager using Playwright Python API for screenshots."""

import asyncio
import os
import tempfile
from typing import Optional
from playwright.async_api import async_playwright, Browser, Page


class BrowserManager:
    """Manages browser automation and screenshot capture using Playwright."""
    
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.server_url = server_url
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None
    
    async def start(self):
        """Initialize browser manager (lazy initialization)."""
        print("Browser manager initialized (lazy mode)")
    
    async def _ensure_browser(self):
        """Ensure browser is started (lazy initialization)."""
        if self.page:
            return  # Already initialized
        
        try:
            # Start Playwright
            self.playwright = await async_playwright().start()
            
            # Launch browser
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--no-sandbox',
                ]
            )
            
            # Create a new page
            self.page = await self.browser.new_page(
                viewport={"width": 1024, "height": 768}
            )
            
            # Navigate to the terminal page
            await self.page.goto(f"{self.server_url}/", wait_until="networkidle")
            
            # Wait for Xterm to initialize
            await self.page.wait_for_selector(".xterm", timeout=5000)
            
            print("Browser initialized and connected to terminal")
            
        except Exception as e:
            print(f"Error starting browser: {e}")
            raise
    
    async def stop(self):
        """Stop the browser."""
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
    
    async def take_screenshot(self) -> str:
        """Take a screenshot of the terminal."""
        # Ensure browser is initialized
        await self._ensure_browser()
        
        if not self.page:
            raise RuntimeError("Browser not initialized")
        
        try:
            # Wait for the terminal to be ready
            await self.page.wait_for_selector(".xterm-screen", timeout=2000)
            
            # Wait longer for content to render and be displayed
            await asyncio.sleep(2.0)
            
            # Take screenshot
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                screenshot_path = f.name
            
            await self.page.screenshot(path=screenshot_path)
            
            return screenshot_path
            
        except Exception as e:
            print(f"Error taking screenshot: {e}")
            raise
