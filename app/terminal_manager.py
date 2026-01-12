import asyncio
import os
import pty
import signal
import fcntl
import struct
import termios
from typing import Dict, Optional, List
from fastapi import WebSocket
import time
from concurrent.futures import ThreadPoolExecutor


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
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.cols = 80
        self.rows = 24
    
    async def start(self):
        """Start the PTY and spawn a shell process."""
        try:
            # Create a PTY
            self.master_fd, self.slave_fd = pty.openpty()
            
            # Fork to create child process
            self.process_pid = os.fork()
            
            if self.process_pid == 0:
                # Child process
                # Close the master FD in the child
                os.close(self.master_fd)
                
                # Create a new session
                os.setsid()
                
                # Make the slave the controlling terminal
                os.dup2(self.slave_fd, 0)  # stdin
                os.dup2(self.slave_fd, 1)  # stdout
                os.dup2(self.slave_fd, 2)  # stderr
                
                # Close the slave FD if it's > 2
                if self.slave_fd > 2:
                    os.close(self.slave_fd)
                
                # Execute bash
                os.execv("/bin/bash", ["/bin/bash"])
                # Never reached
                os._exit(1)
            else:
                # Parent process
                # Close the slave FD in the parent
                os.close(self.slave_fd)
                self.slave_fd = None
                
                # Set the master to non-blocking
                flags = fcntl.fcntl(self.master_fd, fcntl.F_GETFL)
                fcntl.fcntl(self.master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
                
                # Set initial terminal size
                self.resize_pty(self.cols, self.rows)
                
                # Start the read task
                self.read_task = asyncio.create_task(self._read_from_pty_async())
                
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
                # Terminate the process group
                os.killpg(os.getpgid(self.process_pid), signal.SIGTERM)
                try:
                    os.waitpid(self.process_pid, 0)
                except OSError:
                    pass
            except ProcessLookupError:
                pass
            except Exception as e:
                print(f"Error terminating process: {e}")
        
        if self.master_fd is not None:
            try:
                os.close(self.master_fd)
            except OSError:
                pass
        
        self.executor.shutdown(wait=False)
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
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                os.write,
                self.master_fd,
                data.encode('utf-8', errors='replace')
            )
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
            self.cols = cols
            self.rows = rows
            print(f"PTY resized to {cols}x{rows}")
        except OSError as e:
            print(f"Error resizing PTY: {e}")
    
    def _read_blocking(self) -> bytes:
        """Blocking read from PTY (to be run in executor)."""
        try:
            chunk = os.read(self.master_fd, 4096)
            return chunk
        except OSError:
            return b""
    
    async def _read_from_pty_async(self):
        """Continuously read from the PTY and broadcast to WebSocket clients."""
        loop = asyncio.get_event_loop()
        
        while True:
            try:
                # Use executor to do blocking read
                chunk = await loop.run_in_executor(self.executor, self._read_blocking)
                
                if not chunk:
                    # PTY closed
                    await self._broadcast("PTY closed\r\n")
                    break
                
                # Decode and process
                text = chunk.decode('utf-8', errors='replace')
                
                # Broadcast to WebSocket clients
                await self._broadcast(text)
                
                # Update the last output time
                self.last_output_time = time.time()
                self.output_event.set()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in read loop: {e}")
                await asyncio.sleep(0.1)
    
    async def _broadcast(self, data: str):
        """Broadcast data to all connected WebSockets."""
        if len(self.connections) > 0:
            print(f"DEBUG: Broadcasting {len(data)} bytes to {len(self.connections)} connections: {repr(data[:50])}")
        
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
                # Output occurred, continue waiting
            except asyncio.TimeoutError:
                # No output for stable_duration, we're stable
                return
            
            # Check if we've exceeded the total timeout
            if time.time() - start_time >= timeout_seconds:
                return
