# Project Specification: TUI Development MCP Server

## 1. Project Goal

To create a Python-based server that provides an MCP (Model-Context-Protocol) interface for an LLM agent to develop, run, and visually inspect Terminal User Interface (TUI) applications. The server will use a headless browser and a JavaScript terminal emulator (Xterm.js) to render the terminal state and capture high-fidelity PNG screenshots.

## 2. Core Architecture

The system will consist of three main components orchestrated by a central Python application:

- **Python Backend (FastAPI):** The main application that runs the MCP server, manages the pseudo-terminal, and controls the headless browser.
- **Pseudo-Terminal (PTY):** A Python-managed `pty` that runs a standard shell (e.g., `bash`). This is where all commands are executed.
- **Headless Browser Frontend (Playwright + Xterm.js):** A browser instance, invisible to the user, that renders the terminal's state. It connects to the backend via WebSockets.

## 3. Functional Requirements

### 3.1. Python Backend (Server)

- **Framework:** Use `FastAPI` for its modern features, including asynchronous support and built-in WebSocket handling.
- **Pseudo-Terminal Management:**
  - On startup, the server must spawn a child process (e.g., `/bin/bash`) within a pseudo-terminal (`pty`).
  - It must continuously and asynchronously read from the `pty`'s output file descriptor.
  - It must provide a mechanism to write to the `pty`'s input file descriptor.
- **WebSocket Bridge:**
  - Implement a WebSocket endpoint (e.g., `/ws`).
  - When a client (Xterm.js) connects, the server must forward all data read from the `pty` output to the WebSocket client.
  - Conversely, all data received from the WebSocket client must be written to the `pty` input.
  - The server should handle multiple client connections, although the primary use case is a single browser client.
- **Playwright Integration:**
  - The server must launch and manage a single, persistent headless browser instance (`Chromium`) using `playwright.async_api`.
  - On startup, it should instruct the browser to navigate to a local HTML file (`index.html`).
- **Static File Serving:**
  - The server must serve the static assets (`index.html`, `xterm.js`, and related files) required for the browser frontend.

### 3.2. Frontend (Browser-Side)

- **`index.html`:** A minimal HTML file that will host the terminal emulator.
  - It must include the `xterm` and `xterm-addon-fit` libraries.
  - It should contain a single `div` element (e.g., `<div id="terminal"></div>`).
  - It must contain a `<script>` block for initialization.
- **JavaScript Logic (`main.js` or inline script):**
  - Initialize an Xterm.js instance and attach it to the `div` element.
  - Use the `xterm-addon-fit` to make the terminal automatically resize to fill the browser viewport.
  - Establish a WebSocket connection to the backend's `/ws` endpoint.
  - When the WebSocket connection receives data, it must call `terminal.write(data)` to display it.
  - When the Xterm.js instance produces user input (via the `onData` event), it must send that data over the WebSocket to the server.
  - Implement a `ResizeObserver` to detect browser window resizes. On resize, it should refit the terminal and notify the backend of the new `cols` and `rows` so the `pty` can be resized accordingly.

### 3.3. MCP Tool Interface

The `FastAPI` server must expose the following HTTP endpoints for the LLM agent to call. These endpoints will interact with the `pty` and Playwright components.

#### `POST /mcp/run`

- **Purpose:** Execute a command in the terminal.
- **Request Body:** `{ "command": "string" }`
- **Action:** Writes the command string, followed by a newline character (`\n`), to the `pty` input. This is non-blocking.
- **Response:** `{ "status": "command sent" }`

#### `POST /mcp/send_keys`

- **Purpose:** Send a sequence of keystrokes to the terminal.
- **Request Body:** `{ "keys": "string" }`
- **Action:** Writes the raw `keys` string to the `pty` input. This is for sending special characters (like `Ctrl-C`, `\x03`) or interacting with prompts without sending a newline.
- **Response:** `{ "status": "keys sent" }`

#### `GET /mcp/screenshot`

- **Purpose:** Capture a PNG image of the current terminal state.
- **Action:**
  1. Instruct the managed Playwright `page` object to take a screenshot.
  2. The screenshot should be of the entire viewport.
- **Response:** A PNG image file (`image/png`). The image data should be the response body.

#### `POST /mcp/wait_for_stable_output`

- **Purpose:** Wait until the terminal output has stopped changing.
- **Request Body:** `{ "timeout_seconds": int }`
- **Action:**
  1. Monitor the stream of data coming from the `pty`.
  2. If no new data arrives for a short, fixed duration (e.g., 500ms), consider the output stable.
  3. Return successfully. If output continues for the entire `timeout_seconds` duration, return a timeout error.
- **Response:** `{ "status": "output is stable" }` or `{ "status": "error", "message": "timeout waiting for stable output" }`

## 4. Technical Stack

- **Programming Language:** Python 3.10+
- **Web Framework:** FastAPI
- **WebSocket Library:** `websockets` (or FastAPI's native support)
- **Browser Automation:** Playwright for Python (`playwright`)
- **Terminal Emulation (Frontend):** Xterm.js
- **PTY Management:** `pty` and `os` modules (standard library)
- **Async Library:** `asyncio`

## 5. Implementation Plan (Suggested Phasing)

### Phase 1: Basic Setup

- Set up a FastAPI project.
- Create the `index.html` and JavaScript to get a static Xterm.js instance running in the browser.
- Serve these static files from the FastAPI app.

### Phase 2: The WebSocket Bridge

- Implement the `pty` spawning logic in the Python backend.
- Create the `/ws` endpoint.
- Write the async logic to pipe data between the `pty` and the WebSocket. At this point, you should have a working terminal in your browser, controlled by the server.

### Phase 3: Playwright Integration & Screenshots

- Add Playwright to the project.
- Modify the server startup to launch the headless browser and navigate to the local page.
- Implement the `/mcp/screenshot` endpoint.

### Phase 4: Implement MCP Tools

- Build the remaining MCP endpoints: `/mcp/run`, `/mcp/send_keys`, and `/mcp/wait_for_stable_output`.
- Thoroughly test each endpoint to ensure it correctly interacts with the `pty`.

### Phase 5: Refinement

- Implement the terminal resize handling.
- Add robust error handling and logging.
- Package the project with a `requirements.txt` or `pyproject.toml` file.
- Write a `README.md` explaining how to install and run the server.
