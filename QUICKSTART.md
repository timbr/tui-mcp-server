# Quick Start Guide

Get the TUI MCP Server running in 5 minutes.

## Prerequisites

- Python 3.10+
- pip

## Installation (2 minutes)

```bash
# Navigate to the project directory
cd tui-mcp-server

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
python -m playwright install chromium
```

## Start the Server (1 minute)

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

You should see output like:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

## Test the Server (2 minutes)

In a new terminal:

```bash
# Run the test suite
python test_server.py
```

Expected output:
```
==================================================
TUI MCP Server Test Suite
==================================================

=== Testing Health Endpoint ===
✓ Health check passed: {...}

... (more tests)

✓ All tests passed!
```

## Basic Usage

### 1. Run a Command

```bash
curl -X POST http://localhost:8000/mcp/run \
  -H "Content-Type: application/json" \
  -d '{"command": "echo Hello World"}'
```

### 2. Wait for Output

```bash
curl -X POST http://localhost:8000/mcp/wait_for_stable_output \
  -H "Content-Type: application/json" \
  -d '{"timeout_seconds": 5}'
```

### 3. Take a Screenshot

```bash
curl http://localhost:8000/mcp/screenshot -o terminal.png
```

### 4. View the Terminal in Browser

Open your browser and navigate to:
```
http://localhost:8000
```

You'll see a live terminal emulator where you can type commands directly.

## Next Steps

- Read the full [README.md](README.md) for comprehensive documentation
- Check the [API Endpoints](README.md#api-endpoints) section for all available endpoints
- Review the [Usage Example](README.md#usage-example-llm-agent-workflow) for LLM integration
- Explore the [Project Structure](README.md#project-structure) to understand the codebase

## Troubleshooting

### Server won't start

**Error:** `Address already in use`

**Solution:** Change the port:
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### Browser fails to launch

**Error:** `Chromium not found`

**Solution:** Reinstall Playwright:
```bash
python -m playwright install chromium
```

### Tests fail

**Error:** `Connection refused`

**Solution:** Ensure the server is running in another terminal before running tests.

## Architecture at a Glance

```
Your LLM Agent
       ↓
   HTTP/WebSocket
       ↓
   FastAPI Server
       ├─→ PTY (bash shell)
       └─→ Playwright Browser
           └─→ Xterm.js Terminal
```

The server bridges your LLM agent with a real terminal and captures its visual state as PNG screenshots.

## Example: Developing a TUI App

```bash
# 1. Run your TUI app
curl -X POST http://localhost:8000/mcp/run \
  -d '{"command": "python my_app.py"}'

# 2. Wait for it to render
curl -X POST http://localhost:8000/mcp/wait_for_stable_output \
  -d '{"timeout_seconds": 5}'

# 3. See what it looks like
curl http://localhost:8000/mcp/screenshot -o app_state.png

# 4. Interact with it (e.g., press down arrow)
curl -X POST http://localhost:8000/mcp/send_keys \
  -d '{"keys": "\u001b[B"}'

# 5. See the updated state
curl http://localhost:8000/mcp/screenshot -o app_state_2.png
```

## Support

For detailed information, see [README.md](README.md).

For issues, check the troubleshooting section in the README or examine the server logs.
