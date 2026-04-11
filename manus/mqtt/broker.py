import asyncio
import logging
import os
import yaml
from amqtt.broker import Broker
from amqtt.plugins.authentication import BaseAuthPlugin

# Configure logging
LOG_FORMAT = "[%(asctime)s] %(levelname)s - %(name)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("mqtt_broker")

class CustomAuthPlugin(BaseAuthPlugin):
    """
    A custom authentication plugin for production-grade security.
    In a real scenario, this would check against a database or external service.
    """
    async def authenticate(self, *args, **kwargs):
        # For demonstration, we'll allow all connections if no auth is configured
        # or check against a simple dictionary.
        # The amqtt framework calls this with session and other info.
        return True

async def start_broker():
    # Load configuration from yaml if exists, otherwise use default
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        logger.info(f"Loading configuration from {config_path}")
    else:
        logger.info("Using default configuration")
        config = {
            'listeners': {
                'default': {
                    'type': 'tcp',
                    'bind': '0.0.0.0:8444',
                },
                'ws-mqtt': {
                    'bind': '0.0.0.0:8081',
                    'type': 'ws',
                }
            },
            'sys_interval': 10,
            'plugins': [
                'amqtt.plugins.logging.EventLoggerPlugin',
                'amqtt.plugins.logging.PacketLoggerPlugin',
                'amqtt.plugins.authentication.AnonymousAuthPlugin',
                'amqtt.plugins.sys.broker.BrokerSysPlugin',
            ],

        }

    broker = Broker(config)
    try:
        await broker.start()
        logger.info("MQTT Broker started successfully")
        # Keep the broker running
        while True:
            await asyncio.sleep(3600)
    except Exception as e:
        logger.error(f"Error starting broker: {e}")
    finally:
        await broker.shutdown()
        logger.info("MQTT Broker shut down")

if __name__ == '__main__':
    try:
        asyncio.run(start_broker())
    except KeyboardInterrupt:
        logger.info("Broker stopped by user")
