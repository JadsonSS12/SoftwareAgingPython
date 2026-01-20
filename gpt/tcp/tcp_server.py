#!/usr/bin/env python3
import asyncio
import logging
import signal
import sys
from contextlib import suppress
from typing import Optional

import uvloop

# =========================
# Configuration
# =========================
HOST = "0.0.0.0"
PORT = 8888
READ_TIMEOUT = 30          # seconds
MAX_CONNECTIONS = 10_000
LOG_LEVEL = logging.INFO

# =========================
# Logging
# =========================
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("tcp-server")

# =========================
# Connection Handler
# =========================
class TCPServer:
    def __init__(self):
        self._server: Optional[asyncio.AbstractServer] = None
        self._connections = set()
        self._semaphore = asyncio.Semaphore(MAX_CONNECTIONS)

    async def handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ):
        peer = writer.get_extra_info("peername")
        logger.info("Connection opened: %s", peer)

        async with self._semaphore:
            self._connections.add(writer)
            try:
                while True:
                    try:
                        data = await asyncio.wait_for(
                            reader.readline(),
                            timeout=READ_TIMEOUT,
                        )
                    except asyncio.TimeoutError:
                        logger.warning("Read timeout from %s", peer)
                        break

                    if not data:
                        break

                    message = data.decode(errors="ignore").strip()
                    logger.info("Received from %s: %s", peer, message)

                    # ---- APPLICATION LOGIC ----
                    response = f"ACK: {message}\n"
                    writer.write(response.encode())
                    await writer.drain()
                    # ---------------------------

            except Exception:
                logger.exception("Error handling client %s", peer)
            finally:
                self._connections.discard(writer)
                writer.close()
                with suppress(Exception):
                    await writer.wait_closed()
                logger.info("Connection closed: %s", peer)

    async def start(self):
        self._server = await asyncio.start_server(
            self.handle_client,
            HOST,
            PORT,
            reuse_address=True,
            reuse_port=True,
        )

        sockets = self._server.sockets or []
        for sock in sockets:
            logger.info("Listening on %s", sock.getsockname())

    async def stop(self):
        logger.info("Shutting down server...")

        if self._server:
            self._server.close()
            await self._server.wait_closed()

        for writer in list(self._connections):
            writer.close()
            with suppress(Exception):
                await writer.wait_closed()

        logger.info("Shutdown complete")


# =========================
# Application Entry Point
# =========================
async def main():
    server = TCPServer()
    await server.start()

    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def _signal_handler():
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _signal_handler)

    await stop_event.wait()
    await server.stop()


if __name__ == "__main__":
    # uvloop = production-grade event loop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
