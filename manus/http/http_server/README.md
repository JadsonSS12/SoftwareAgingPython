# Robust HTTP/HTTPS Server

A production-grade HTTP/HTTPS server implementation using **FastAPI** and **Uvicorn** ASGI server.

## Features

- ✅ **Modern Framework**: Built with FastAPI, one of the fastest Python web frameworks
- ✅ **Production Server**: Uvicorn ASGI server with multi-worker support
- ✅ **HTTP & HTTPS**: Full support for both protocols with SSL/TLS
- ✅ **Request Validation**: Automatic request/response validation with Pydantic
- ✅ **API Documentation**: Auto-generated interactive API docs (Swagger UI & ReDoc)
- ✅ **Middleware Support**: CORS, GZip compression, request timing
- ✅ **Error Handling**: Comprehensive error handling with custom handlers
- ✅ **Logging**: Structured logging for monitoring and debugging
- ✅ **Async Support**: Full async/await support for high performance
- ✅ **Health Checks**: Built-in health check endpoint for monitoring

## Requirements

- Python 3.11+
- Dependencies listed in `requirements.txt`

## Installation

1. Install dependencies:
```bash
pip3 install -r requirements.txt
```

Or with sudo (system-wide):
```bash
sudo pip3 install -r requirements.txt
```

## Quick Start

### HTTP Server (Development)

Run the server in development mode with auto-reload:

```bash
python3 app.py
```

The server will start on `http://0.0.0.0:8000`

### HTTP Server (Production)

Run with production settings and multiple workers:

```bash
python3 server.py
```

Or with custom options:

```bash
python3 server.py --host 0.0.0.0 --port 8000 --workers 4
```

### HTTPS Server

1. Generate a self-signed certificate (for testing):

```bash
python3 server.py --generate-cert
```

2. Run the HTTPS server:

```bash
python3 server.py --https
```

The server will start on `https://0.0.0.0:8443`

For production, use certificates from a trusted CA (Let's Encrypt, etc.):

```bash
python3 server.py --https --cert /path/to/cert.pem --key /path/to/key.pem
```

## Available Endpoints

### Root
- **GET /** - HTML landing page with server information

### Health Check
- **GET /health** - Health check endpoint for monitoring
  ```json
  {
    "status": "healthy",
    "timestamp": "2026-01-10T12:00:00",
    "uptime": 123.45
  }
  ```

### Server Info
- **GET /api/info** - Get server information and available endpoints

### Message Echo
- **POST /api/message** - Echo message endpoint
  
  Request body:
  ```json
  {
    "message": "Hello, World!",
    "metadata": {
      "key": "value"
    }
  }
  ```
  
  Response:
  ```json
  {
    "success": true,
    "echo": "Hello, World!",
    "received_at": "2026-01-10T12:00:00",
    "metadata": {
      "key": "value"
    }
  }
  ```

### API Documentation
- **GET /docs** - Interactive API documentation (Swagger UI)
- **GET /redoc** - Alternative API documentation (ReDoc)

## Testing the Server

### Using curl

Test health endpoint:
```bash
curl http://localhost:8000/health
```

Test message endpoint:
```bash
curl -X POST http://localhost:8000/api/message \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, Server!"}'
```

Test HTTPS (with self-signed cert):
```bash
curl -k https://localhost:8443/health
```

### Using Python requests

```python
import requests

# Health check
response = requests.get("http://localhost:8000/health")
print(response.json())

# Send message
response = requests.post(
    "http://localhost:8000/api/message",
    json={"message": "Hello from Python!", "metadata": {"source": "test"}}
)
print(response.json())
```

### Using Browser

Open your browser and navigate to:
- http://localhost:8000 - Main page
- http://localhost:8000/docs - Interactive API documentation
- http://localhost:8000/health - Health check

## Command Line Options

```
python3 server.py [OPTIONS]

Options:
  --host HOST           Host to bind (default: 0.0.0.0)
  --port PORT           Port to bind (default: 8000 for HTTP, 8443 for HTTPS)
  --workers N           Number of worker processes (default: 4)
  --https               Enable HTTPS with SSL/TLS
  --cert FILE           SSL certificate file (default: cert.pem)
  --key FILE            SSL private key file (default: key.pem)
  --generate-cert       Generate self-signed SSL certificate and exit
  -h, --help            Show help message
```

## Architecture

### Technology Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **Uvicorn**: Lightning-fast ASGI server implementation
- **Pydantic**: Data validation using Python type annotations
- **Python 3.11**: Latest Python with performance improvements

### Middleware Chain

1. **CORS Middleware**: Handles cross-origin requests
2. **GZip Middleware**: Compresses responses > 1KB
3. **Timing Middleware**: Adds X-Process-Time header to responses

### Request Flow

```
Client Request
    ↓
Middleware Chain (CORS → GZip → Timing)
    ↓
Route Handler
    ↓
Pydantic Validation
    ↓
Business Logic
    ↓
Response Formatting
    ↓
Middleware Chain (reverse)
    ↓
Client Response
```

## Production Deployment

### Systemd Service

Create `/etc/systemd/system/http-server.service`:

```ini
[Unit]
Description=Robust HTTP Server
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/path/to/http_server
Environment="PATH=/usr/bin"
ExecStart=/usr/bin/python3 /path/to/http_server/server.py --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable http-server
sudo systemctl start http-server
```

### Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["python3", "server.py", "--workers", "4"]
```

Build and run:
```bash
docker build -t http-server .
docker run -p 8000:8000 http-server
```

### Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Performance Tuning

### Worker Count

Set workers based on CPU cores:
```bash
# For CPU-bound tasks: workers = (2 × CPU cores) + 1
python3 server.py --workers 9  # For 4 CPU cores
```

### Uvicorn Options

For maximum performance, use uvicorn directly with additional options:

```bash
uvicorn app:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --loop uvloop \
  --http httptools \
  --log-level info \
  --access-log \
  --use-colors
```

## Security Considerations

1. **HTTPS in Production**: Always use HTTPS with valid certificates
2. **CORS Configuration**: Restrict `allow_origins` to specific domains
3. **Rate Limiting**: Consider adding rate limiting middleware
4. **Input Validation**: Leverage Pydantic models for all inputs
5. **Security Headers**: Add security headers (HSTS, CSP, etc.)
6. **Secrets Management**: Use environment variables for sensitive data

## Monitoring

### Health Check Endpoint

Monitor server health:
```bash
curl http://localhost:8000/health
```

### Logs

Uvicorn provides structured logs with:
- Request method and path
- Response status code
- Processing time
- Client IP address

### Metrics

Consider integrating:
- Prometheus for metrics collection
- Grafana for visualization
- Sentry for error tracking

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 8000
sudo lsof -i :8000

# Kill the process
sudo kill -9 <PID>
```

### SSL Certificate Issues

For self-signed certificates, use `-k` flag with curl:
```bash
curl -k https://localhost:8443/health
```

### Permission Denied

Run with sudo or use port > 1024:
```bash
python3 server.py --port 8080
```

## License

MIT License - feel free to use in your projects.

## Contributing

Contributions welcome! Please submit pull requests or open issues.
