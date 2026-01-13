# TUI Development MCP Server

A Python-based MCP (Model-Context-Protocol) server that enables LLM agents to develop, run, and visually inspect Terminal User Interface (TUI) applications. The server uses a headless browser with Xterm.js to render terminal output and capture high-fidelity PNG screenshots.

## Architecture Overview

The system consists of three main components:

1. **Python Backend (FastAPI):** Manages the MCP server, pseudo-terminal, and browser automation.
2. **Pseudo-Terminal (PTY):** Runs a bash shell where commands are executed.
3. **Headless Browser Frontend (Playwright + Xterm.js):** Renders the terminal state and enables screenshot capture.

### Data Flow

**For Screenshots:**
```
LLM Agent → HTTP API → FastAPI Server → PTY → Output Buffer
                                            ↓
                                       Playwright
                                            ↓
                                  Xterm.js (direct injection)
                                            ↓
                                      PNG Screenshot
```

**For Real-Time Terminal (Optional):**
```
LLM Agent → WebSocket → FastAPI Server → PTY
                            ↓
                    Browser with Xterm.js
```

**Note:** Screenshots do NOT require WebSocket connections. Terminal output is buffered in memory and injected directly into the browser via Playwright. See `docs/WEBSOCKET_DECISION.md` for details.

## Installation

### Prerequisites

- Python 3.10 or higher
- pip package manager
- Linux/macOS (Windows support may require additional configuration)

### Setup

1. **Clone or navigate to the project directory:**
   ```bash
   cd tui-mcp-server
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright browsers:**
   ```bash
   python -m playwright install chromium
   ```

## Running the Server

Start the server with:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The server will start on `http://localhost:8000`.

### Verification

Check the server health:

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "terminal_ready": true,
  "browser_ready": true
}
```

## API Endpoints

### Terminal Endpoints

#### `POST /mcp/run`

Execute a command in the terminal.

**Request:**
```bash
curl -X POST http://localhost:8000/mcp/run \
  -H "Content-Type: application/json" \
  -d '{"command": "ls -la"}'
```

**Response:**
```json
{"status": "command sent"}
```

#### `POST /mcp/send_keys`

Send keystrokes to the terminal (useful for interactive prompts or special keys).

**Request:**
```bash
curl -X POST http://localhost:8000/mcp/send_keys \
  -H "Content-Type: application/json" \
  -d '{"keys": "\u0003"}'  # Ctrl-C
```

**Response:**
```json
{"status": "keys sent"}
```

Special keys:
- `\x03` - Ctrl-C (interrupt)
- `\x04` - Ctrl-D (EOF)
- `\n` - Enter
- `\t` - Tab

#### `POST /mcp/wait_for_stable_output`

Wait for the terminal output to stabilize (useful before taking screenshots).

**Request:**
```bash
curl -X POST http://localhost:8000/mcp/wait_for_stable_output \
  -H "Content-Type: application/json" \
  -d '{"timeout_seconds": 5}'
```

**Response:**
```json
{"status": "output is stable"}
```

#### `GET /mcp/screenshot`

Capture a PNG screenshot of the current terminal state.

**Request:**
```bash
curl http://localhost:8000/mcp/screenshot -o terminal.png
```

**Response:** PNG image file

### Health Check

#### `GET /health`

Check the server status.

**Request:**
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "terminal_ready": true,
  "browser_ready": true
}
```

## Usage Example: LLM Agent Workflow

Here's how an LLM agent would use the server to develop a TUI application:

### 1. Run a TUI Application

```bash
curl -X POST http://localhost:8000/mcp/run \
  -H "Content-Type: application/json" \
  -d '{"command": "python3 my_tui_app.py"}'
```

### 2. Wait for Output to Stabilize

```bash
curl -X POST http://localhost:8000/mcp/wait_for_stable_output \
  -H "Content-Type: application/json" \
  -d '{"timeout_seconds": 5}'
```

### 3. Capture a Screenshot

```bash
curl http://localhost:8000/mcp/screenshot -o current_state.png
```

### 4. Interact with the App (Send Keystrokes)

```bash
# Send arrow key down
curl -X POST http://localhost:8000/mcp/send_keys \
  -H "Content-Type: application/json" \
  -d '{"keys": "\u001b[B"}'  # ESC [ B (arrow down)
```

### 5. Stop the App

```bash
curl -X POST http://localhost:8000/mcp/send_keys \
  -H "Content-Type: application/json" \
  -d '{"keys": "\u0003"}'  # Ctrl-C
```

## WebSocket Connection (Real-Time Terminal)

For real-time terminal interaction, connect to the WebSocket endpoint:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
    console.log('Connected');
    ws.send('echo "Hello from WebSocket"\n');
};

ws.onmessage = (event) => {
    console.log('Terminal output:', event.data);
};
```

## Project Structure

```
tui-mcp-server/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI application and endpoints
│   ├── terminal_manager.py          # PTY management and output buffering
│   └── browser_manager.py           # Playwright browser management
├── static/
│   ├── index.html                   # WebSocket-based real-time terminal UI
│   ├── terminal-screenshot.html     # Screenshot page (no WebSocket)
│   ├── main.js                      # Xterm.js WebSocket integration
│   └── lib/                         # Xterm.js library files
│       ├── xterm.js
│       ├── xterm.css
│       └── xterm-addon-fit.js
├── docs/
│   └── WEBSOCKET_DECISION.md        # Why WebSockets aren't needed for screenshots
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

## Key Features

- **High-Fidelity Screenshots:** Captures terminal output with colors and styling intact using Playwright + Xterm.js.
- **No WebSocket Required for Screenshots:** Direct content injection via Playwright for fast, reliable screenshots.
- **Real-Time Terminal (Optional):** WebSocket-based real-time terminal interaction for interactive sessions.
- **PTY Management:** Proper pseudo-terminal handling with signal management and output buffering.
- **Asynchronous I/O:** Built on asyncio for efficient concurrent operations.
- **Containerization-Ready:** Browser configured with single-process mode for containerized environments.
- **Error Handling:** Robust error handling and logging.

## Troubleshooting

### Browser fails to start

**Issue:** Playwright browser fails to launch.

**Solution:** Ensure Chromium is installed:
```bash
python -m playwright install chromium
```

### PTY connection fails

**Issue:** "Terminal manager not initialized" error.

**Solution:** Ensure the server has fully started. Check the console output for any errors.

### Screenshot is blank

**Issue:** Screenshot captures a blank terminal.

**Solution:** 
1. Ensure the terminal has had time to render. Use `/mcp/wait_for_stable_output` before taking a screenshot.
2. Check that a command has been executed: `curl -X POST http://localhost:8000/mcp/run -H "Content-Type: application/json" -d '{"command": "echo test"}'`

### WebSocket connection refused

**Issue:** WebSocket connection fails.

**Solution:** Ensure the server is running and the URL is correct. Check firewall settings.

## Development Notes

### Adding New MCP Tools

To add a new MCP tool:

1. Add the endpoint to `app/main.py`
2. Implement the logic in the appropriate manager class
3. Update the documentation

### Modifying Terminal Behavior

Terminal behavior can be customized in `app/terminal_manager.py`:
- Initial terminal size: `self.resize_pty(80, 24)`
- Shell command: Change `/bin/bash` to another shell
- Output buffer size: Modify the read buffer size in `_read_from_pty()`

### Browser Configuration

Browser settings can be adjusted in `app/browser_manager.py`:
- Viewport size: Modify `viewport` parameter
- Browser launch arguments: Adjust the `args` list
- Screenshot directory: Change `screenshot_dir`

## Performance Considerations

- **Screenshot Latency:** First screenshot may take longer due to browser initialization.
- **Memory Usage:** The browser instance consumes significant memory. For resource-constrained environments, consider using a lighter terminal emulator.
- **Network Latency:** For remote deployments, consider using a reverse proxy with compression.

## Security Considerations

- **No Authentication:** The current implementation has no authentication. Use a reverse proxy (nginx, etc.) to add authentication in production.
- **Command Execution:** The server executes arbitrary commands in the PTY. Restrict access accordingly.
- **File Access:** Screenshots are stored in a temporary directory. Ensure proper cleanup.

## License

This project is provided as-is for development and research purposes.

## Support

For issues or questions, refer to the troubleshooting section or check the server logs for detailed error messages.
