# Docker Quick Reference - TUI MCP Server

## One-Liner Deployment

```bash
docker-compose up -d
```

That's it! The server will be running at `http://localhost:8000`.

## Essential Commands

### Start/Stop

```bash
# Start the server
docker-compose up -d

# Stop the server
docker-compose down

# Restart the server
docker-compose restart
```

### View Logs

```bash
# Real-time logs
docker-compose logs -f

# Last 50 lines
docker-compose logs --tail=50
```

### Test the Server

```bash
# Health check
curl http://localhost:8000/health

# Run full test suite
docker-compose exec tui-mcp-server python test_server.py
```

### Build & Run Manually

```bash
# Build the image
docker build -t tui-mcp-server:latest .

# Run the container
docker run -d -p 8000:8000 --name tui-mcp-server tui-mcp-server:latest

# Stop the container
docker stop tui-mcp-server

# Remove the container
docker rm tui-mcp-server
```

## File Structure

```
tui-mcp-server/
├── Dockerfile                    # Container image definition
├── docker-compose.yml            # Multi-container orchestration
├── .dockerignore                 # Files to exclude from build
└── DOCKER_DEPLOYMENT.md          # Full deployment guide
```

## What Gets Deployed

- **Base Image:** Python 3.11 slim (minimal dependencies)
- **Runtime:** FastAPI + Uvicorn
- **Browser:** Chromium (via Playwright)
- **Terminal:** Xterm.js
- **Port:** 8000 (configurable)

## Configuration

### Change Port

Edit `docker-compose.yml`:
```yaml
ports:
  - "8001:8000"  # Access on port 8001
```

### Add Environment Variables

Create `.env` file:
```
LOG_LEVEL=DEBUG
PYTHONUNBUFFERED=1
```

Use with Docker Compose:
```bash
docker-compose --env-file .env up -d
```

### Resource Limits

Edit `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 1G
```

## Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs tui-mcp-server

# Rebuild without cache
docker-compose build --no-cache
```

### Port already in use

```bash
# Find what's using the port
lsof -i :8000

# Use a different port in docker-compose.yml
```

### Out of memory

```bash
# Check memory usage
docker stats tui-mcp-server

# Increase limit in docker-compose.yml
```

## Testing

### Quick Test

```bash
# After starting the server
curl http://localhost:8000/health
```

### Full Test Suite

```bash
docker-compose exec tui-mcp-server python test_server.py
```

### Manual API Test

```bash
# Run a command
curl -X POST http://localhost:8000/mcp/run \
  -H "Content-Type: application/json" \
  -d '{"command": "echo Hello"}'

# Take a screenshot
curl http://localhost:8000/mcp/screenshot -o screenshot.png

# Send keystrokes
curl -X POST http://localhost:8000/mcp/send_keys \
  -H "Content-Type: application/json" \
  -d '{"keys": "echo test\n"}'
```

## Production Deployment

### With Nginx Reverse Proxy

```bash
docker-compose --profile production up -d
```

This starts both the TUI MCP Server and Nginx.

### On Cloud Platforms

**AWS ECS:**
```bash
docker tag tui-mcp-server:latest <account>.dkr.ecr.<region>.amazonaws.com/tui-mcp-server
docker push <account>.dkr.ecr.<region>.amazonaws.com/tui-mcp-server
```

**Google Cloud Run:**
```bash
gcloud builds submit --tag gcr.io/project/tui-mcp-server
gcloud run deploy tui-mcp-server --image gcr.io/project/tui-mcp-server
```

**Kubernetes:**
```bash
kubectl apply -f k8s-deployment.yaml
```

## Cleanup

```bash
# Stop and remove containers
docker-compose down

# Remove images
docker rmi tui-mcp-server:latest

# Remove all unused Docker resources
docker system prune -a
```

## Performance

- **Image Size:** ~1.5GB (mostly Chromium)
- **Memory Usage:** ~500MB base + application overhead
- **CPU Usage:** Minimal when idle
- **Startup Time:** ~8 seconds

## Security

- Non-root user (appuser)
- Dropped unnecessary capabilities
- Resource limits enforced
- Health checks enabled
- Restart policies configured

## Next Steps

1. Start the server: `docker-compose up -d`
2. Verify it's running: `curl http://localhost:8000/health`
3. Run tests: `docker-compose exec tui-mcp-server python test_server.py`
4. Read full guide: See `DOCKER_DEPLOYMENT.md`

## Support

For detailed information, see:
- `DOCKER_DEPLOYMENT.md` - Complete deployment guide
- `README.md` - Application documentation
- `QUICKSTART.md` - Quick start guide
