# Quick Start Guide

## Installation

```bash
# Install dependencies
pip3 install -r requirements.txt
```

## Running the Server

### Option 1: Development Mode (Auto-reload)

```bash
python3 app.py
```

Server will start at: http://0.0.0.0:8000

### Option 2: Production Mode (HTTP)

```bash
python3 server.py
```

Or with custom options:

```bash
python3 server.py --host 0.0.0.0 --port 8000 --workers 4
```

### Option 3: Production Mode (HTTPS)

Generate self-signed certificate:

```bash
python3 server.py --generate-cert
```

Start HTTPS server:

```bash
python3 server.py --https
```

Server will start at: https://0.0.0.0:8443

## Testing

Run the comprehensive test suite:

```bash
python3 test_server.py http
```

Or test individual endpoints:

```bash
# Health check
curl http://localhost:8000/health

# Server info
curl http://localhost:8000/api/info

# Send message
curl -X POST http://localhost:8000/api/message \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, Server!"}'
```

## API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Available Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | / | HTML landing page |
| GET | /health | Health check |
| GET | /api/info | Server information |
| POST | /api/message | Echo message |
| GET | /docs | Swagger UI documentation |
| GET | /redoc | ReDoc documentation |

## Command Line Options

```
python3 server.py --help

Options:
  --host HOST           Host to bind (default: 0.0.0.0)
  --port PORT           Port to bind (default: 8000 for HTTP, 8443 for HTTPS)
  --workers N           Number of worker processes (default: 4)
  --https               Enable HTTPS with SSL/TLS
  --cert FILE           SSL certificate file (default: cert.pem)
  --key FILE            SSL private key file (default: key.pem)
  --generate-cert       Generate self-signed SSL certificate and exit
```

## Project Structure

```
http_server/
├── app.py              # Main FastAPI application
├── server.py           # Production server runner
├── test_server.py      # Comprehensive test suite
├── requirements.txt    # Python dependencies
├── README.md           # Full documentation
├── QUICKSTART.md       # This file
├── cert.pem           # SSL certificate (generated)
└── key.pem            # SSL private key (generated)
```

## Next Steps

1. Read the full [README.md](README.md) for detailed documentation
2. Explore the interactive API docs at http://localhost:8000/docs
3. Customize the endpoints in `app.py` for your use case
4. Deploy to production with proper SSL certificates
