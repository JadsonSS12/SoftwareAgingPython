import asyncio
import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("TCPClient")

async def tcp_echo_client(message: str, host: str = "127.0.0.1", port: int = 3002):
    try:
        reader, writer = await asyncio.open_connection(host, port)
        
        logger.info(f"Sending: {message!r}")
        writer.write(message.encode())
        await writer.drain()

        data = await reader.read(100)
        logger.info(f"Received: {data.decode()!r}")

        logger.info("Closing connection")
        writer.close()
        await writer.wait_closed()
    except Exception as e:
        logger.error(f"Client error: {e}")

if __name__ == "__main__":
    msg = sys.argv[1] if len(sys.argv) > 1 else "Hello World!"
    asyncio.run(tcp_echo_client(msg))
