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
        if self.browser:
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
                    '--disable-setuid-sandbox',
                    '--disable-software-rasterizer',
                    '--single-process',  # Prevent multi-process crashes
                ]
            )

            print("Browser initialized")

        except Exception as e:
            print(f"Error starting browser: {e}")
            raise
    
    async def stop(self):
        """Stop the browser."""
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
    
    async def take_screenshot(self, terminal_content: str, cols: int = 80, rows: int = 24) -> str:
        """Take a screenshot of the terminal with injected content.

        Args:
            terminal_content: The terminal output to render
            cols: Number of columns
            rows: Number of rows

        Returns:
            Path to the screenshot file
        """
        # Ensure browser is initialized
        await self._ensure_browser()

        if not self.browser:
            raise RuntimeError("Browser not initialized")

        try:
            # Create a new page for this screenshot
            page = await self.browser.new_page(
                viewport={"width": 1024, "height": 768}
            )

            try:
                # Navigate to the screenshot page
                print(f"Navigating to {self.server_url}/static/terminal-screenshot.html")
                await page.goto(f"{self.server_url}/static/terminal-screenshot.html", wait_until="load")

                # Wait for xterm.js to load and initialize terminal in one call
                print("Waiting for Terminal class and initializing...")
                await page.wait_for_function("typeof Terminal !== 'undefined'", timeout=5000)
                print("Terminal class loaded")

                # Initialize and write content in a single evaluate call to avoid multiple round-trips
                print(f"Initializing terminal ({cols}x{rows}) and writing {len(terminal_content)} bytes")
                print(f"Content preview: {repr(terminal_content[:100] if terminal_content else '')}")

                result = await page.evaluate("""
                    ({ cols, rows, content }) => {
                        try {
                            // Initialize terminal
                            const terminal = new Terminal({
                                cursorBlink: true,
                                cursorStyle: 'block',
                                fontSize: 14,
                                fontFamily: 'Courier New, monospace',
                                theme: {
                                    background: '#000000',
                                    foreground: '#ffffff',
                                    cursor: '#ffffff',
                                },
                                scrollback: 1000,
                                convertEol: true,
                                allowTransparency: false,
                                cols: cols,
                                rows: rows,
                            });

                            const container = document.getElementById('terminal');
                            terminal.open(container);

                            // Write content if provided
                            if (content) {
                                terminal.write(content);
                            }

                            return { success: true, contentLength: content ? content.length : 0 };
                        } catch (error) {
                            return { success: false, error: error.message };
                        }
                    }
                """, {"cols": cols, "rows": rows, "content": terminal_content})

                print(f"Result: {result}")
                if not result.get("success"):
                    raise RuntimeError(f"Terminal initialization failed: {result.get('error')}")

                # Small delay to ensure rendering is complete
                await asyncio.sleep(0.5)

                # Take screenshot
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                    screenshot_path = f.name

                await page.screenshot(path=screenshot_path)

                print(f"Screenshot saved to {screenshot_path}")
                return screenshot_path

            finally:
                # Always close the page
                await page.close()

        except Exception as e:
            print(f"Error taking screenshot: {e}")
            raise
