"""
Robust TCP Server using FastAPI with Uvicorn
Production-ready TCP server implementation
"""

import asyncio
import logging
import signal
import sys
import json
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import uvicorn
from starlette.responses import JSONResponse

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('tcp_server.log')
    ]
)
logger = logging.getLogger(__name__)


# ==================== Data Models ====================
class Message(BaseModel):
    """Message model for client communication"""
    content: str = Field(..., min_length=1, max_length=1000)
    message_type: str = Field(default="text", regex="^(text|command|data)$")
    client_id: Optional[str] = None


class ServerStatus(BaseModel):
    """Server status model"""
    status: str
    connected_clients: int
    messages_processed: int
    uptime_seconds: float


# ==================== TCP Server Core ====================
class TCPServer:
    """Asynchronous TCP Server handling multiple client connections"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8888):
        self.host = host
        self.port = port
        self.server: Optional[asyncio.Server] = None
        self.connected_clients: Dict[str, asyncio.StreamWriter] = {}
        self.messages_processed = 0
        self.start_time = asyncio.get_event_loop().time()
        
    async def handle_client(self, reader: asyncio.StreamReader, 
                           writer: asyncio.StreamWriter):
        """Handle individual client connection"""
        client_addr = writer.get_extra_info('peername')
        client_id = f"{client_addr[0]}:{client_addr[1]}"
        
        logger.info(f"New connection from {client_id}")
        self.connected_clients[client_id] = writer
        
        try:
            while True:
                # Read data from client
                data = await reader.read(1024)
                if not data:
                    break
                
                # Process the received data
                await self.process_message(client_id, data, writer)
                self.messages_processed += 1
                
        except asyncio.CancelledError:
            logger.info(f"Connection cancelled for {client_id}")
        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}")
        finally:
            # Clean up client connection
            await self.cleanup_client(client_id, writer)
    
    async def process_message(self, client_id: str, data: bytes, 
                            writer: asyncio.StreamWriter):
        """Process incoming message from client"""
        try:
            # Decode and parse message
            message_str = data.decode('utf-8').strip()
            
            # Try to parse as JSON
            try:
                message_data = json.loads(message_str)
                message = Message(**message_data)
            except:
                message = Message(content=message_str)
            
            logger.info(f"Received from {client_id}: {message.content}")
            
            # Echo back with processing confirmation
            response = {
                "status": "processed",
                "original_content": message.content,
                "processed_by": "tcp_server",
                "timestamp": asyncio.get_event_loop().time()
            }
            
            writer.write(json.dumps(response).encode('utf-8') + b'\n')
            await writer.drain()
            
        except Exception as e:
            logger.error(f"Error processing message from {client_id}: {e}")
            error_response = json.dumps({
                "status": "error",
                "message": str(e)
            })
            writer.write(error_response.encode('utf-8') + b'\n')
            await writer.drain()
    
    async def cleanup_client(self, client_id: str, writer: asyncio.StreamWriter):
        """Clean up client connection"""
        if client_id in self.connected_clients:
            del self.connected_clients[client_id]
        
        try:
            writer.close()
            await writer.wait_closed()
            logger.info(f"Connection closed for {client_id}")
        except Exception as e:
            logger.error(f"Error closing connection for {client_id}: {e}")
    
    async def start(self):
        """Start the TCP server"""
        try:
            self.server = await asyncio.start_server(
                self.handle_client,
                self.host,
                self.port
            )
            
            addr = self.server.sockets[0].getsockname()
            logger.info(f"TCP Server started on {addr}")
            
            async with self.server:
                await self.server.serve_forever()
                
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise
    
    async def stop(self):
        """Stop the TCP server gracefully"""
        logger.info("Stopping TCP server...")
        
        # Close all client connections
        for client_id, writer in list(self.connected_clients.items()):
            await self.cleanup_client(client_id, writer)
        
        # Close the server
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        
        logger.info("TCP server stopped")
    
    def get_status(self) -> ServerStatus:
        """Get current server status"""
        current_time = asyncio.get_event_loop().time()
        return ServerStatus(
            status="running" if self.server else "stopped",
            connected_clients=len(self.connected_clients),
            messages_processed=self.messages_processed,
            uptime_seconds=current_time - self.start_time
        )


# ==================== FastAPI Application ====================
# Global TCP server instance
tcp_server: Optional[TCPServer] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global tcp_server
    
    # Startup
    logger.info("Starting application...")
    
    # Initialize TCP server
    tcp_server = TCPServer()
    
    # Start TCP server in background task
    server_task = asyncio.create_task(tcp_server.start())
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    
    # Cancel server task
    server_task.cancel()
    try:
        await server_task
    except asyncio.CancelledError:
        pass
    
    # Stop TCP server
    if tcp_server:
        await tcp_server.stop()

# Create FastAPI application
app = FastAPI(
    title="Robust TCP Server",
    description="Production-ready TCP Server with HTTP API",
    version="1.0.0",
    lifespan=lifespan
)


# ==================== API Endpoints ====================
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "TCP Server API",
        "endpoints": {
            "status": "/status",
            "health": "/health",
            "send_message": "/send (POST)"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "tcp_server"}


@app.get("/status")
async def get_status():
    """Get TCP server status"""
    if not tcp_server:
        raise HTTPException(status_code=503, detail="Server not initialized")
    
    status = tcp_server.get_status()
    return JSONResponse(content=status.dict())


@app.post("/send")
async def send_message(message: Message):
    """
    Send a message through the TCP server (simulated)
    In production, this would route to specific clients
    """
    if not tcp_server:
        raise HTTPException(status_code=503, detail="Server not initialized")
    
    # Process message through server logic
    logger.info(f"API received message: {message.content}")
    
    return {
        "status": "queued",
        "message": message.content,
        "client_count": len(tcp_server.connected_clients)
    }


@app.get("/clients")
async def list_clients():
    """List connected clients"""
    if not tcp_server:
        raise HTTPException(status_code=503, detail="Server not initialized")
    
    clients = list(tcp_server.connected_clients.keys())
    return {"clients": clients, "count": len(clients)}


# ==================== Signal Handlers ====================
def handle_shutdown(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)


# ==================== Configuration ====================
class Config:
    """Server configuration"""
    HOST = "0.0.0.0"
    TCP_PORT = 8888
    HTTP_PORT = 8000
    WORKERS = 4
    LOG_LEVEL = "info"


# ==================== Main Entry Point ====================
if __name__ == "__main__":
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    
    # Configuration for Uvicorn
    config = uvicorn.Config(
        app,
        host=Config.HOST,
        port=Config.HTTP_PORT,
        workers=Config.WORKERS,
        log_level=Config.LOG_LEVEL,
        access_log=True,
        timeout_keep_alive=30,
    )
    
    server = uvicorn.Server(config)
    
    logger.info(f"""
    ============================================
    TCP Server Starting...
    HTTP API: http://{Config.HOST}:{Config.HTTP_PORT}
    TCP Socket: {Config.HOST}:{Config.TCP_PORT}
    Workers: {Config.WORKERS}
    Log Level: {Config.LOG_LEVEL}
    ============================================
    """)
    
    try:
        server.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)