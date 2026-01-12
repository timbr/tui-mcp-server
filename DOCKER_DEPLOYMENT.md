# Docker Deployment Guide for TUI MCP Server

This guide provides comprehensive instructions for deploying the TUI Development MCP Server using Docker and Docker Compose.

## Prerequisites

- Docker installed (version 20.10+)
- Docker Compose installed (version 1.29+)
- At least 2GB of available RAM
- At least 2GB of available disk space

### Installation

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose
sudo usermod -aG docker $USER
```

**macOS (with Homebrew):**
```bash
brew install docker docker-compose
```

**Windows (with WSL2):**
```bash
wsl --install
# Then install Docker Desktop for Windows
```

## Quick Start (5 minutes)

### Option 1: Using Docker Compose (Recommended)

The easiest way to get started:

```bash
# Clone or navigate to the project directory
cd tui-mcp-server

# Build and start the container
docker-compose up -d

# Verify the server is running
curl http://localhost:8000/health

# View logs
docker-compose logs -f
```

The server will be available at `http://localhost:8000`.

### Option 2: Using Docker CLI

If you prefer to use Docker directly:

```bash
# Build the image
docker build -t tui-mcp-server:latest .

# Run the container
docker run -d \
  --name tui-mcp-server \
  -p 8000:8000 \
  --restart unless-stopped \
  tui-mcp-server:latest

# Check if it's running
docker ps | grep tui-mcp-server

# View logs
docker logs -f tui-mcp-server
```

## Configuration

### Environment Variables

Create a `.env` file in the project directory to customize settings:

```bash
# Server configuration
PORT=8000
HOST=0.0.0.0

# Python configuration
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1

# Logging
LOG_LEVEL=INFO
```

Then use it with Docker Compose:

```bash
docker-compose --env-file .env up -d
```

### Resource Limits

Edit `docker-compose.yml` to adjust resource limits:

```yaml
deploy:
  resources:
    limits:
      cpus: '2'        # Maximum 2 CPUs
      memory: 1G       # Maximum 1GB RAM
    reservations:
      cpus: '1'        # Reserve 1 CPU
      memory: 512M     # Reserve 512MB RAM
```

## Common Operations

### Start the Server

```bash
docker-compose up -d
```

### Stop the Server

```bash
docker-compose down
```

### View Logs

```bash
# Real-time logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100

# Logs from specific service
docker-compose logs tui-mcp-server
```

### Restart the Server

```bash
docker-compose restart
```

### Execute Commands in Container

```bash
# Open a shell
docker-compose exec tui-mcp-server /bin/bash

# Run a command
docker-compose exec tui-mcp-server python -c "import sys; print(sys.version)"
```

### Remove Everything

```bash
# Stop and remove containers
docker-compose down

# Also remove volumes
docker-compose down -v

# Also remove images
docker-compose down -v --rmi all
```

## Testing the Deployment

### Health Check

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

### Test All Endpoints

```bash
# Run the test suite inside the container
docker-compose exec tui-mcp-server python test_server.py
```

### Manual Testing

```bash
# Test /mcp/run endpoint
curl -X POST http://localhost:8000/mcp/run \
  -H "Content-Type: application/json" \
  -d '{"command": "echo Hello from Docker"}'

# Test /mcp/screenshot endpoint
curl http://localhost:8000/mcp/screenshot -o screenshot.png

# Test /mcp/send_keys endpoint
curl -X POST http://localhost:8000/mcp/send_keys \
  -H "Content-Type: application/json" \
  -d '{"keys": "echo test\n"}'

# Test /mcp/wait_for_stable_output endpoint
curl -X POST http://localhost:8000/mcp/wait_for_stable_output \
  -H "Content-Type: application/json" \
  -d '{"timeout_seconds": 5}'
```

## Production Deployment

### Using Nginx Reverse Proxy

For production deployments, use the included Nginx configuration:

```bash
# Start with the production profile
docker-compose --profile production up -d
```

This will start both the TUI MCP Server and an Nginx reverse proxy.

**Configure SSL/TLS:**

1. Create an `ssl` directory:
```bash
mkdir -p ssl
```

2. Place your SSL certificates:
```bash
cp /path/to/cert.pem ssl/cert.pem
cp /path/to/key.pem ssl/key.pem
```

3. Create `nginx.conf`:
```nginx
events {
    worker_connections 1024;
}

http {
    upstream tui_mcp_server {
        server tui-mcp-server:8000;
    }

    server {
        listen 80;
        server_name _;
        return 301 https://$host$request_uri;
    }

    server {
        listen 443 ssl;
        server_name your-domain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        location / {
            proxy_pass http://tui_mcp_server;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }
}
```

### Security Best Practices

1. **Use a non-root user** (already configured in Dockerfile)
2. **Drop unnecessary capabilities** (already configured in docker-compose.yml)
3. **Use read-only filesystems where possible**
4. **Set resource limits** (already configured in docker-compose.yml)
5. **Use environment variables for secrets** (not hardcoded)
6. **Enable Docker Content Trust**
7. **Regularly update base images**

### Monitoring and Logging

**View container metrics:**
```bash
docker stats tui-mcp-server
```

**Configure log rotation:**
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

**Use external logging:**
```yaml
logging:
  driver: "splunk"
  options:
    splunk-token: "${SPLUNK_TOKEN}"
    splunk-url: "https://your-splunk-instance.com"
```

## Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs tui-mcp-server

# Verify image was built
docker images | grep tui-mcp-server

# Rebuild the image
docker-compose build --no-cache
```

### Port already in use

```bash
# Find what's using port 8000
lsof -i :8000

# Use a different port in docker-compose.yml
ports:
  - "8001:8000"
```

### Out of memory

```bash
# Check container memory usage
docker stats tui-mcp-server

# Increase memory limit in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 2G
```

### Browser not starting in container

The Dockerfile includes all necessary dependencies for Chromium. If issues persist:

```bash
# Rebuild without cache
docker-compose build --no-cache

# Check for missing libraries
docker-compose exec tui-mcp-server ldd /root/.local/lib/python3.11/site-packages/playwright/driver/chromium/chrome
```

### WebSocket connection issues

Ensure your reverse proxy (if used) supports WebSocket upgrades:

```nginx
proxy_http_version 1.1;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

## Deployment Platforms

### Docker Hub

Push your image to Docker Hub:

```bash
# Login
docker login

# Tag the image
docker tag tui-mcp-server:latest your-username/tui-mcp-server:latest

# Push
docker push your-username/tui-mcp-server:latest
```

### AWS ECS

```bash
# Create ECR repository
aws ecr create-repository --repository-name tui-mcp-server

# Tag and push
docker tag tui-mcp-server:latest <account-id>.dkr.ecr.<region>.amazonaws.com/tui-mcp-server:latest
docker push <account-id>.dkr.ecr.<region>.amazonaws.com/tui-mcp-server:latest
```

### Google Cloud Run

```bash
# Build and push
gcloud builds submit --tag gcr.io/your-project/tui-mcp-server

# Deploy
gcloud run deploy tui-mcp-server \
  --image gcr.io/your-project/tui-mcp-server \
  --platform managed \
  --region us-central1 \
  --memory 1Gi \
  --cpu 2
```

### Kubernetes

Create a `k8s-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tui-mcp-server
spec:
  replicas: 1
  selector:
    matchLabels:
      app: tui-mcp-server
  template:
    metadata:
      labels:
        app: tui-mcp-server
    spec:
      containers:
      - name: tui-mcp-server
        image: your-registry/tui-mcp-server:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 40
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 20
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: tui-mcp-server
spec:
  selector:
    app: tui-mcp-server
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

Deploy with:
```bash
kubectl apply -f k8s-deployment.yaml
```

## Performance Optimization

### Multi-stage Build

The Dockerfile uses a multi-stage build to reduce image size:
- Builder stage: Compiles dependencies
- Final stage: Only includes runtime requirements

### Image Size

```bash
# Check image size
docker images tui-mcp-server

# Typical size: ~1.5GB (mostly Chromium)
```

### Build Caching

To speed up builds:

```bash
# Use BuildKit for better caching
DOCKER_BUILDKIT=1 docker build -t tui-mcp-server:latest .
```

## Maintenance

### Regular Updates

```bash
# Pull latest base image
docker pull python:3.11-slim

# Rebuild
docker-compose build --no-cache

# Restart
docker-compose up -d
```

### Backup

```bash
# Backup volumes
docker run --rm -v tui-mcp-server_screenshots:/data -v $(pwd):/backup \
  alpine tar czf /backup/screenshots-backup.tar.gz -C /data .
```

### Cleanup

```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Remove unused networks
docker network prune
```

## Support

For issues or questions:

1. Check the logs: `docker-compose logs -f`
2. Review the troubleshooting section above
3. Check the main README.md for application-specific issues
4. Verify Docker and Docker Compose versions
5. Ensure sufficient system resources are available

## Summary

The Docker deployment provides:

✓ Consistent environment across systems
✓ Easy scaling and management
✓ Isolated dependencies
✓ Production-ready configuration
✓ Security best practices
✓ Comprehensive monitoring and logging

The TUI MCP Server is now ready for deployment in any Docker-compatible environment.
