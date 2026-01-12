import asyncio
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


# Create FastAPI app
app = FastAPI(title="TUI MCP Server", version="1.0.0", lifespan=lifespan)

# Mount static files
static_dir = Path(__file__).parent.parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def root():
    """Serve the main HTML page."""
    return FileResponse(static_dir / "index.html")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for terminal I/O."""
    await websocket.accept()
    
    if not terminal_manager:
        await websocket.close(code=1011, reason="Terminal manager not initialized")
        return
    
    # Register the WebSocket connection
    connection_id = terminal_manager.add_connection(websocket)
    
    try:
        while True:
            # Receive data from the client
            data = await websocket.receive_text()
            
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
    
    except WebSocketDisconnect:
        terminal_manager.remove_connection(connection_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        terminal_manager.remove_connection(connection_id)


@app.post("/mcp/run")
async def mcp_run(command: str):
    """Execute a command in the terminal."""
    if not terminal_manager:
        raise HTTPException(status_code=503, detail="Terminal manager not initialized")
    
    await terminal_manager.write_to_pty(command + "\n")
    return {"status": "command sent"}


@app.post("/mcp/send_keys")
async def mcp_send_keys(keys: str):
    """Send keystrokes to the terminal."""
    if not terminal_manager:
        raise HTTPException(status_code=503, detail="Terminal manager not initialized")
    
    await terminal_manager.write_to_pty(keys)
    return {"status": "keys sent"}


@app.get("/mcp/screenshot")
async def mcp_screenshot():
    """Capture a PNG screenshot of the terminal."""
    if not browser_manager:
        raise HTTPException(status_code=503, detail="Browser manager not initialized")
    
    screenshot_path = await browser_manager.take_screenshot()
    
    if not screenshot_path or not os.path.exists(screenshot_path):
        raise HTTPException(status_code=500, detail="Failed to capture screenshot")
    
    return FileResponse(screenshot_path, media_type="image/png")


@app.post("/mcp/wait_for_stable_output")
async def mcp_wait_for_stable_output(timeout_seconds: int = 5):
    """Wait for terminal output to stabilize."""
    if not terminal_manager:
        raise HTTPException(status_code=503, detail="Terminal manager not initialized")
    
    try:
        await terminal_manager.wait_for_stable_output(timeout_seconds)
        return {"status": "output is stable"}
    except asyncio.TimeoutError:
        return {"status": "error", "message": "timeout waiting for stable output"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "terminal_ready": terminal_manager is not None,
        "browser_ready": browser_manager is not None,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
