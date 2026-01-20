import asyncio
import logging
from amqtt.broker import Broker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

BROKER_CONFIG = {
    "listeners": {
        "default": {
            "type": "tcp",
            "bind": "0.0.0.0:1883",
        },
        # Uncomment to enable MQTT over WebSocket
        # "ws": {
        #     "type": "ws",
        #     "bind": "0.0.0.0:8080",
        # }
    },
    "sys_interval": 10,
    "topic-check": {
        "enabled": True
    },
    "auth": {
        "allow-anonymous": True
    },
    "plugins": {
        "packet_logger": {
            "enabled": False
        }
    }
}


class MQTTBrokerServer:
    def __init__(self):
        self.broker = Broker(BROKER_CONFIG)

    async def start(self):
        logging.info("Starting MQTT Broker...")
        await self.broker.start()

    async def shutdown(self):
        logging.info("Shutting down MQTT Broker...")
        await self.broker.shutdown()


async def main():
    server = MQTTBrokerServer()
    await server.start()

    try:
        # Keep broker alive forever
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        pass
    finally:
        await server.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
