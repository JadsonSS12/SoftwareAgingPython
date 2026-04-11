import logging
import anyio
from anyio.abc import SocketStream

# Setup structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(process)d - %(message)s"
)
logger = logging.getLogger(__name__)

async def handle_client(stream: SocketStream):
    """
    Handles an individual TCP client connection.
    AnyIO's 'async with' ensures the stream is closed automatically.
    """
    addr = stream.extra(anyio.abc.SocketAttribute.remote_address)
    logger.info(f"New connection from {addr}")
    
    try:
        async with stream:
            while True:
                try:
                    # Receive data (buffer size 1024)
                    data = await stream.receive(1024)
                    if not data:
                        break
                    
                    logger.debug(f"Received from {addr}: {data.decode().strip()}")
                    
                    # Echo back the data
                    await stream.send(data)
                except anyio.EndOfStream:
                    break
    except Exception as e:
        logger.error(f"Error handling {addr}: {e}")
    finally:
        logger.info(f"Connection closed: {addr}")

async def main():
    """
    Main entry point for the TCP server.
    """
    port = 3001
    # create_tcp_listener provides a robust listener with dual-stack support
    listener = await anyio.create_tcp_listener(local_port=port)
    
    logger.info(f"TCP Server running on port {port})")
    
    async with listener:
        # Task groups ensure all handlers finish or cancel correctly
        await listener.serve(handle_client)

if __name__ == "__main__":
    try:
        anyio.run(main)
    except KeyboardInterrupt:
        logger.info("Server stopped by user.")