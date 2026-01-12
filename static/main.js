// Initialize Xterm.js terminal with proper configuration
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
});

// Initialize the fit addon
const fitAddon = new FitAddon();
terminal.loadAddon(fitAddon);

// Get the terminal container
const terminalContainer = document.getElementById('terminal');

// Open the terminal in the container
terminal.open(terminalContainer);

// Fit the terminal to the container
fitAddon.fit();

// Log terminal initialization
console.log('Terminal initialized with dimensions:', terminal.cols, 'x', terminal.rows);

// Establish WebSocket connection
const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const ws = new WebSocket(`${protocol}//${window.location.host}/ws`);

ws.onopen = () => {
    console.log('WebSocket connected');
    terminal.write('Connected to TUI MCP Server\r\n');
    terminal.write('Waiting for shell...\r\n');
};

ws.onmessage = (event) => {
    // Receive data from the server and write it to the terminal
    console.log('Received data:', event.data.length, 'bytes');
    terminal.write(event.data);
};

ws.onerror = (error) => {
    console.error('WebSocket error:', error);
    terminal.write('\r\n[ERROR] WebSocket connection failed\r\n');
};

ws.onclose = () => {
    console.log('WebSocket disconnected');
    terminal.write('\r\n[DISCONNECTED] WebSocket connection closed\r\n');
};

// Send terminal input to the server
terminal.onData((data) => {
    console.log('Sending data:', data.length, 'bytes');
    if (ws.readyState === WebSocket.OPEN) {
        ws.send(data);
    } else {
        console.warn('WebSocket not open, cannot send data');
    }
});

// Handle terminal resize
const resizeObserver = new ResizeObserver(() => {
    fitAddon.fit();
    const { cols, rows } = terminal;
    console.log('Terminal resized to:', cols, 'x', rows);
    
    // Send resize information to the server
    if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'resize', cols, rows }));
    }
});

resizeObserver.observe(terminalContainer);

// Initial fit and resize notification
window.addEventListener('load', () => {
    console.log('Window loaded, fitting terminal');
    fitAddon.fit();
    const { cols, rows } = terminal;
    console.log('Initial terminal size:', cols, 'x', rows);
    
    if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'resize', cols, rows }));
    }
});

// Handle window resize
window.addEventListener('resize', () => {
    console.log('Window resized, fitting terminal');
    fitAddon.fit();
    const { cols, rows } = terminal;
    
    if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'resize', cols, rows }));
    }
});

// Ensure terminal is visible and focused
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM content loaded');
    terminal.focus();
});

// Log when the page is fully loaded
window.addEventListener('load', () => {
    console.log('Page fully loaded');
    console.log('Terminal ready for input');
});
