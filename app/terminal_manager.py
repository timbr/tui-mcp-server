import asyncio
import os
import pty
import subprocess
import signal
import fcntl
import struct
import termios
from typing import Dict, Optional, Set
from fastapi import WebSocket
import time


class TerminalManager:
    """Manages the pseudo-terminal (PTY) and WebSocket connections."""
    
    def __init__(self):
        self.master_fd: Optional[int] = None
        self.slave_fd: Optional[int] = None
        self.process_pid: Optional[int] = None
        self.connections: Dict[str, WebSocket] = {}
        self.connection_counter = 0
        self.read_task: Optional[asyncio.Task] = None
        self.last_output_time = time.time()
        self.output_event = asyncio.Event()
    
    async def start(self):
        """Start the PTY and spawn a shell process."""
        try:
            # Fork and create a pseudo-terminal
            self.process_pid, self.master_fd = pty.openpty()
            
            if self.process_pid == 0:
                # Child process
                # Create a new session
                os.setsid()
                
                # Open the slave side of the PTY
                slave_fd = os.open(os.ttyname(self.master_fd), os.O_RDWR)
                
                # Duplicate the slave FD to stdin, stdout, stderr
                os.dup2(slave_fd, 0)
                os.dup2(slave_fd, 1)
                os.dup2(slave_fd, 2)
                
                # Close the original slave FD
                if slave_fd > 2:
                    os.close(slave_fd)
                
                # Execute the shell
                os.execv("/bin/bash", ["/bin/bash"])
            else:
                # Parent process
                # Set the PTY to non-blocking mode
                flags = fcntl.fcntl(self.master_fd, fcntl.F_GETFL)
                fcntl.fcntl(self.master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
                
                # Set initial terminal size
                self.resize_pty(80, 24)
                
                # Start the read task
                self.read_task = asyncio.create_task(self._read_from_pty())
                
                print(f"PTY started with PID {self.process_pid}")
        except Exception as e:
            print(f"Error starting PTY: {e}")
            raise
    
    async def stop(self):
        """Stop the PTY and terminate the shell process."""
        if self.read_task:
            self.read_task.cancel()
            try:
                await self.read_task
            except asyncio.CancelledError:
                pass
        
        if self.process_pid:
            try:
                os.kill(self.process_pid, signal.SIGTERM)
                # Wait a bit for graceful shutdown
                await asyncio.sleep(0.5)
                try:
                    os.kill(self.process_pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            except ProcessLookupError:
                pass
        
        if self.master_fd is not None:
            try:
                os.close(self.master_fd)
            except OSError:
                pass
        
        print("PTY stopped")
    
    def add_connection(self, websocket: WebSocket) -> str:
        """Add a WebSocket connection."""
        connection_id = f"conn_{self.connection_counter}"
        self.connection_counter += 1
        self.connections[connection_id] = websocket
        print(f"Connection added: {connection_id}")
        return connection_id
    
    def remove_connection(self, connection_id: str):
        """Remove a WebSocket connection."""
        if connection_id in self.connections:
            del self.connections[connection_id]
            print(f"Connection removed: {connection_id}")
    
    async def write_to_pty(self, data: str):
        """Write data to the PTY."""
        if self.master_fd is None:
            return
        
        try:
            os.write(self.master_fd, data.encode('utf-8', errors='replace'))
        except OSError as e:
            print(f"Error writing to PTY: {e}")
    
    def resize_pty(self, cols: int, rows: int):
        """Resize the PTY."""
        if self.master_fd is None:
            return
        
        try:
            # Set the terminal size
            s = struct.pack('HHHH', rows, cols, 0, 0)
            fcntl.ioctl(self.master_fd, termios.TIOCSWINSZ, s)
            print(f"PTY resized to {cols}x{rows}")
        except OSError as e:
            print(f"Error resizing PTY: {e}")
    
    async def _read_from_pty(self):
        """Continuously read from the PTY and broadcast to all connections."""
        buffer = b""
        
        while True:
            try:
                # Read from the PTY
                chunk = os.read(self.master_fd, 4096)
                
                if not chunk:
                    # PTY closed
                    await self._broadcast("PTY closed\r\n")
                    break
                
                # Decode and broadcast
                text = chunk.decode('utf-8', errors='replace')
                await self._broadcast(text)
                
                # Update the last output time
                self.last_output_time = time.time()
                self.output_event.set()
                
            except BlockingIOError:
                # No data available, yield control
                await asyncio.sleep(0.01)
            except OSError as e:
                print(f"Error reading from PTY: {e}")
                break
            except Exception as e:
                print(f"Unexpected error in read loop: {e}")
                break
    
    async def _broadcast(self, data: str):
        """Broadcast data to all connected WebSockets."""
        disconnected = []
        
        for connection_id, websocket in self.connections.items():
            try:
                await websocket.send_text(data)
            except Exception as e:
                print(f"Error sending to {connection_id}: {e}")
                disconnected.append(connection_id)
        
        # Clean up disconnected connections
        for connection_id in disconnected:
            self.remove_connection(connection_id)
    
    async def wait_for_stable_output(self, timeout_seconds: int = 5):
        """Wait for the terminal output to stabilize."""
        stable_duration = 0.5  # Consider stable if no output for 500ms
        start_time = time.time()
        
        while time.time() - start_time < timeout_seconds:
            # Clear the event
            self.output_event.clear()
            
            # Wait for either output or timeout
            try:
                await asyncio.wait_for(self.output_event.wait(), timeout=stable_duration)
                # Output occurred, reset the timer
            except asyncio.TimeoutError:
                # No output for stable_duration, we're stable
                return
            
            # Check if we've exceeded the total timeout
            if time.time() - start_time >= timeout_seconds:
                raise asyncio.TimeoutError("Timeout waiting for stable output")
        
        raise asyncio.TimeoutError("Timeout waiting for stable output")
