// Initialize Xterm.js terminal
const terminal = new Terminal({
    cursorBlink: true,
    cursorStyle: 'block',
    fontSize: 14,
    fontFamily: 'Courier New, monospace',
    theme: {
        background: '#000000',
        foreground: '#ffffff',
    },
    scrollback: 1000,
});

// Initialize the fit addon
const fitAddon = new FitAddon();
terminal.loadAddon(fitAddon);

// Attach terminal to the DOM
const terminalContainer = document.getElementById('terminal');
terminal.open(terminalContainer);

// Fit the terminal to the container
fitAddon.fit();

// Establish WebSocket connection
const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const ws = new WebSocket(`${protocol}//${window.location.host}/ws`);

ws.onopen = () => {
    console.log('WebSocket connected');
    terminal.write('Connected to TUI MCP Server\r\n');
};

ws.onmessage = (event) => {
    // Receive data from the server and write it to the terminal
    terminal.write(event.data);
};

ws.onerror = (error) => {
    console.error('WebSocket error:', error);
    terminal.write('\r\nWebSocket error: Connection failed\r\n');
};

ws.onclose = () => {
    console.log('WebSocket disconnected');
    terminal.write('\r\nWebSocket disconnected\r\n');
};

// Send terminal input to the server
terminal.onData((data) => {
    if (ws.readyState === WebSocket.OPEN) {
        ws.send(data);
    }
});

// Handle terminal resize
const resizeObserver = new ResizeObserver(() => {
    fitAddon.fit();
    const { cols, rows } = terminal;
    // Send resize information to the server
    if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'resize', cols, rows }));
    }
});

resizeObserver.observe(terminalContainer);

// Initial fit
window.addEventListener('load', () => {
    fitAddon.fit();
    const { cols, rows } = terminal;
    if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'resize', cols, rows }));
    }
});

// Handle window resize
window.addEventListener('resize', () => {
    fitAddon.fit();
    const { cols, rows } = terminal;
    if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'resize', cols, rows }));
    }
});
