"""
Robust HTTP/HTTPS Server Implementation
Using FastAPI with Uvicorn ASGI server
"""

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import logging
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title="Robust HTTP/HTTPS Server",
    description="Production-grade HTTP/HTTPS server built with FastAPI and Uvicorn",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add GZip middleware for response compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.4f}s")
    return response

# Pydantic models for request/response validation
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    uptime: float

class MessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    metadata: Optional[Dict[str, Any]] = None

class MessageResponse(BaseModel):
    success: bool
    echo: str
    received_at: str
    metadata: Optional[Dict[str, Any]] = None

# Application state
app_start_time = time.time()

# Root endpoint
@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with HTML response"""
    html_content = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Robust HTTP/HTTPS Server</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 50px auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }
                .container {
                    background-color: white;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                h1 {
                    color: #333;
                }
                .endpoint {
                    background-color: #f9f9f9;
                    padding: 10px;
                    margin: 10px 0;
                    border-left: 4px solid #007bff;
                }
                code {
                    background-color: #e9ecef;
                    padding: 2px 6px;
                    border-radius: 3px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 Robust HTTP/HTTPS Server</h1>
                <p>Production-grade server built with <strong>FastAPI</strong> and <strong>Uvicorn</strong></p>
                
                <h2>Available Endpoints:</h2>
                
                <div class="endpoint">
                    <strong>GET /health</strong><br>
                    Health check endpoint
                </div>
                
                <div class="endpoint">
                    <strong>GET /api/info</strong><br>
                    Server information
                </div>
                
                <div class="endpoint">
                    <strong>POST /api/message</strong><br>
                    Echo message endpoint (JSON body required)
                </div>
                
                <div class="endpoint">
                    <strong>GET /docs</strong><br>
                    Interactive API documentation (Swagger UI)
                </div>
                
                <div class="endpoint">
                    <strong>GET /redoc</strong><br>
                    Alternative API documentation (ReDoc)
                </div>
                
                <h2>Quick Test:</h2>
                <p>Try: <code>curl http://localhost:8000/health</code></p>
            </div>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for monitoring"""
    uptime = time.time() - app_start_time
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        uptime=uptime
    )

# Server info endpoint
@app.get("/api/info")
async def server_info():
    """Get server information"""
    return {
        "server": "FastAPI + Uvicorn",
        "version": "1.0.0",
        "python_version": "3.11",
        "features": [
            "HTTPS/TLS support",
            "Request/Response validation",
            "CORS middleware",
            "GZip compression",
            "Request timing",
            "Automatic API documentation",
            "Async/await support"
        ],
        "endpoints": {
            "root": "/",
            "health": "/health",
            "info": "/api/info",
            "message": "/api/message",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }

# Message echo endpoint
@app.post("/api/message", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def process_message(message_data: MessageRequest):
    """Process and echo message"""
    logger.info(f"Received message: {message_data.message}")
    
    return MessageResponse(
        success=True,
        echo=message_data.message,
        received_at=datetime.utcnow().isoformat(),
        metadata=message_data.metadata
    )

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"The requested path {request.url.path} was not found",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    """Custom 500 handler"""
    logger.error(f"Internal error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("🚀 Server starting up...")
    logger.info("FastAPI application initialized successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("🛑 Server shutting down...")
    logger.info("Cleanup completed")

if __name__ == "__main__":
    import uvicorn
    
    # Run with uvicorn (HTTP only for testing)
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
