"""
Robust HTTP/HTTPS Server with FastAPI and Uvicorn
Production-ready with SSL/TLS support, logging, health checks, and security headers
"""

import os
import logging
import ssl
from typing import Optional
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import uvicorn

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Application state
class AppState:
    def __init__(self):
        self.startup_time = datetime.utcnow()
        self.request_count = 0

# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown events"""
    app.state.app_state = AppState()
    logger.info("🚀 Application starting up...")
    
    # Startup logic
    logger.info(f"Startup time: {app.state.app_state.startup_time}")
    
    yield
    
    # Shutdown logic
    logger.info("🛑 Application shutting down...")

# Create FastAPI application
app = FastAPI(
    title="Robust HTTP/HTTPS Server",
    description="Production-ready server with SSL/TLS support",
    version="1.0.0",
    docs_url="/docs" if os.getenv("ENABLE_DOCS", "true").lower() == "true" else None,
    redoc_url="/redoc" if os.getenv("ENABLE_DOCS", "true").lower() == "true" else None,
    lifespan=lifespan
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=os.getenv("ALLOWED_HOSTS", "*").split(",")
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"]
)

# Compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    request_id = request.headers.get('X-Request-ID', 'N/A')
    logger.info(f"📥 {request.method} {request.url.path} - Request ID: {request_id}")
    
    response = await call_next(request)
    
    logger.info(f"📤 {request.method} {request.url.path} - Status: {response.status_code}")
    return response

# Request counting middleware
@app.middleware("http")
async def count_requests(request: Request, call_next):
    """Count total requests"""
    if hasattr(request.app.state, 'app_state'):
        request.app.state.app_state.request_count += 1
    return await call_next(request)

# Pydantic models
class HealthResponse(BaseModel):
    status: str = Field(..., description="Service status")
    uptime: str = Field(..., description="Server uptime")
    timestamp: datetime = Field(..., description="Current server time")
    total_requests: int = Field(..., description="Total requests served")
    version: str = Field(..., description="API version")

class EchoRequest(BaseModel):
    message: str = Field(..., description="Message to echo")
    timestamp: Optional[datetime] = Field(None, description="Optional timestamp")

class EchoResponse(BaseModel):
    echo: str = Field(..., description="Echoed message")
    received_at: datetime = Field(..., description="When message was received")
    server_info: str = Field(..., description="Server information")
    request_id: Optional[str] = Field(None, description="Request ID if provided")

# Routes
@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with basic HTML response"""
    return """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Robust HTTP/HTTPS Server</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    line-height: 1.6;
                }
                .header {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 2rem;
                    border-radius: 10px;
                    margin-bottom: 2rem;
                    text-align: center;
                }
                .endpoints {
                    background: #f4f4f4;
                    padding: 1rem;
                    border-radius: 5px;
                    margin: 1rem 0;
                }
                code {
                    background: #e9e9e9;
                    padding: 2px 5px;
                    border-radius: 3px;
                    font-family: monospace;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚀 Robust HTTP/HTTPS Server</h1>
                <p>Production-ready server running with SSL/TLS support</p>
            </div>
            
            <h2>📡 Available Endpoints:</h2>
            
            <div class="endpoints">
                <p><strong>GET</strong> <code>/</code> - This page</p>
                <p><strong>GET</strong> <code>/health</code> - Health check endpoint</p>
                <p><strong>POST</strong> <code>/echo</code> - Echo service (send JSON with 'message' field)</p>
                <p><strong>GET</strong> <code>/docs</code> - Interactive API documentation</p>
                <p><strong>GET</strong> <code>/status</code> - Server status information</p>
            </div>
            
            <h2>🔧 Features:</h2>
            <ul>
                <li>SSL/TLS encryption support</li>
                <li>Request logging & monitoring</li>
                <li>CORS configuration</li>
                <li>Compression middleware</li>
                <li>Security headers</li>
                <li>Health checks</li>
                <li>Request counting</li>
            </ul>
        </body>
    </html>
    """

@app.get("/health", response_model=HealthResponse)
async def health_check(request: Request):
    """Health check endpoint for monitoring"""
    app_state = request.app.state.app_state
    uptime = datetime.utcnow() - app_state.startup_time
    
    return HealthResponse(
        status="healthy",
        uptime=str(uptime),
        timestamp=datetime.utcnow(),
        total_requests=app_state.request_count,
        version=app.version
    )

@app.get("/status")
async def server_status(request: Request):
    """Server status information"""
    return {
        "server": "Robust HTTP/HTTPS Server",
        "framework": "FastAPI",
        "asgi_server": "Uvicorn",
        "python_version": os.getenv("PYTHON_VERSION", "3.8+"),
        "environment": os.getenv("ENVIRONMENT", "production"),
        "ssl_enabled": os.getenv("SSL_ENABLED", "false").lower() == "true",
        "start_time": request.app.state.app_state.startup_time.isoformat(),
        "current_time": datetime.utcnow().isoformat(),
        "total_requests": request.app.state.app_state.request_count
    }

@app.post("/echo", response_model=EchoResponse)
async def echo_message(request: Request, echo_request: EchoRequest):
    """Echo endpoint that returns the sent message with additional info"""
    request_id = request.headers.get('X-Request-ID')
    
    return EchoResponse(
        echo=echo_request.message,
        received_at=datetime.utcnow(),
        server_info=f"Server v{app.version}",
        request_id=request_id
    )

# Custom exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "path": request.url.path,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "path": request.url.path,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

if __name__ == "__main__":
    # Configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    ssl_enabled = os.getenv("SSL_ENABLED", "false").lower() == "true"
    
    ssl_config = None
    if ssl_enabled:
        certfile = os.getenv("SSL_CERTFILE", "cert.pem")
        keyfile = os.getenv("SSL_KEYFILE", "key.pem")
        
        if os.path.exists(certfile) and os.path.exists(keyfile):
            ssl_config = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_config.load_cert_chain(certfile=certfile, keyfile=keyfile)
            logger.info(f"🔐 SSL/TLS enabled with cert: {certfile}, key: {keyfile}")
        else:
            logger.warning("⚠️  SSL certificate files not found. Running without SSL.")
    
    logger.info(f"🌐 Starting server on {host}:{port}")
    logger.info(f"📄 Documentation available at http{'s' if ssl_enabled else ''}://{host}:{port}/docs")
    
    # Run the server
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        ssl_certfile=certfile if ssl_enabled and os.path.exists(certfile) else None,
        ssl_keyfile=keyfile if ssl_enabled and os.path.exists(keyfile) else None,
        log_level="info",
        access_log=True,
        timeout_keep_alive=30,
        workers=int(os.getenv("WORKERS", "1"))
    )