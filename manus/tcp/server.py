import asyncio
import logging
import signal
import sys
from typing import Optional

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("TCPServer")

class RobustTCPServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 3001):
        self.host = host
        self.port = port
        self.server: Optional[asyncio.AbstractServer] = None
        self._stop_event = asyncio.Event()

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        addr = writer.get_extra_info('peername')
        logger.info(f"New connection from {addr}")
        
        try:
            while not self._stop_event.is_set():
                data = await reader.read(1024)
                if not data:
                    logger.info(f"Connection closed by {addr}")
                    break
                
                message = data.decode().strip()
                logger.debug(f"Received {message!r} from {addr}")
                
                # Echo back the message
                response = f"Echo: {message}\n"
                writer.write(response.encode())
                await writer.drain()
                
        except asyncio.CancelledError:
            logger.info(f"Connection with {addr} cancelled")
        except Exception as e:
            logger.error(f"Error handling client {addr}: {e}")
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
            logger.info(f"Closed connection for {addr}")

    async def start(self):
        self.server = await asyncio.start_server(
            self.handle_client, self.host, self.port
        )
        
        addr = self.server.sockets[0].getsockname()
        logger.info(f"Serving on {addr}")

        async with self.server:
            # Wait until the stop event is set
            await self._stop_event.wait()
            logger.info("Stopping server...")
            self.server.close()
            await self.server.wait_closed()
            logger.info("Server stopped.")

    def stop(self):
        self._stop_event.set()

async def main():
    server = RobustTCPServer()
    
    # Handle signals for graceful shutdown
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, server.stop)
    
    try:
        await server.start()
    except Exception as e:
        logger.critical(f"Server failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
