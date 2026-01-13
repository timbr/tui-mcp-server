#!/usr/bin/env python3
import os
import pty
import subprocess
import signal
import fcntl
import struct
import termios
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
import uvicorn

from app.terminal_manager import TerminalManager
from app.browser_manager import BrowserManager


# Global instances
terminal_manager: Optional[TerminalManager] = None
browser_manager: Optional[BrowserManager] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""
    global terminal_manager, browser_manager
    
    # Startup
    print("Starting TUI MCP Server...")
    terminal_manager = TerminalManager()
    await terminal_manager.start()
    
    browser_manager = BrowserManager()
    await browser_manager.start()
    
    print("Server started successfully")
    yield
    
    # Shutdown
    print("Shutting down TUI MCP Server...")
    if terminal_manager:
        await terminal_manager.stop()
    if browser_manager:
        await browser_manager.stop()
    print("Server shut down")


# Create the FastAPI app
app = FastAPI(lifespan=lifespan)

# Mount static files
app.mount("/lib", StaticFiles(directory="static/lib"), name="lib")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for terminal I/O."""
    await websocket.accept()
    
    if not terminal_manager:
        await websocket.close(code=1011, reason="Terminal manager not initialized")
        return
    
    # Register the WebSocket connection
    connection_id = terminal_manager.add_connection(websocket)
    print(f"WebSocket connection registered: {connection_id}")
    
    try:
        # Keep the connection open and handle incoming data
        while True:
            try:
                # Receive data from the client (with timeout to allow graceful shutdown)
                import asyncio
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
                
                # Check if it's a resize message
                if data.startswith('{"type":"resize"'):
                    import json
                    try:
                        msg = json.loads(data)
                        cols = msg.get('cols', 80)
                        rows = msg.get('rows', 24)
                        terminal_manager.resize_pty(cols, rows)
                    except json.JSONDecodeError:
                        pass
                else:
                    # Send regular input to the PTY
                    await terminal_manager.write_to_pty(data)
            except asyncio.TimeoutError:
                # Timeout is OK, just continue the loop
                continue
    
    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {connection_id}")
        terminal_manager.remove_connection(connection_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        terminal_manager.remove_connection(connection_id)


@app.get("/")
async def root():
    """Serve the terminal page."""
    return FileResponse("static/index.html")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "terminal_ready": terminal_manager is not None,
        "browser_ready": browser_manager is not None
    }


class CommandRequest(BaseModel):
    command: str


@app.post("/mcp/run")
async def mcp_run(request: CommandRequest):
    """Execute a command in the terminal."""
    if not terminal_manager:
        raise HTTPException(status_code=503, detail="Terminal manager not initialized")
    
    await terminal_manager.write_to_pty(request.command + "\n")
    return {"status": "command sent"}


class KeysRequest(BaseModel):
    keys: str


@app.post("/mcp/send_keys")
async def mcp_send_keys(request: KeysRequest):
    """Send keystrokes to the terminal."""
    if not terminal_manager:
        raise HTTPException(status_code=503, detail="Terminal manager not initialized")
    
    await terminal_manager.write_to_pty(request.keys)
    return {"status": "keys sent"}


class WaitRequest(BaseModel):
    timeout_seconds: int = 5


@app.post("/mcp/wait_for_stable_output")
async def mcp_wait_for_stable_output(request: WaitRequest):
    """Wait for terminal output to stabilize."""
    if not terminal_manager:
        raise HTTPException(status_code=503, detail="Terminal manager not initialized")
    
    await terminal_manager.wait_for_stable_output(request.timeout_seconds)
    return {"status": "output is stable"}


@app.get("/mcp/screenshot")
async def mcp_screenshot():
    """Take a screenshot of the terminal."""
    if not browser_manager:
        raise HTTPException(status_code=503, detail="Browser manager not initialized")

    if not terminal_manager:
        raise HTTPException(status_code=503, detail="Terminal manager not initialized")

    # Get the buffered terminal content
    terminal_content = terminal_manager.get_output_content()

    # Get terminal dimensions
    cols = terminal_manager.cols
    rows = terminal_manager.rows

    # Take screenshot with the content
    screenshot_path = await browser_manager.take_screenshot(terminal_content, cols, rows)

    if not screenshot_path or not os.path.exists(screenshot_path):
        raise HTTPException(status_code=500, detail="Failed to take screenshot")

    # Return the screenshot as a PNG file
    return FileResponse(screenshot_path, media_type="image/png")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
