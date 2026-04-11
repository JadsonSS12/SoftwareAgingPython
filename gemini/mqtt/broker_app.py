import logging
import asyncio
import os
from amqtt.broker import Broker

# Configure logging for production visibility
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Broker Configuration
# In production, move these to a YAML file or environment variables
config = {
    'listeners': {
        'default': {
            'type': 'tcp',
            'bind': '0.0.0.0:1884', # Standard MQTT port
            'max_connections': 1000,
        },
        'ws': {
            'type': 'ws',
            'bind': '0.0.0.0:8083', # MQTT over WebSockets
        }
    },
    'sys_interval': 10,
    'auth': {
        'allow-anonymous': True, # Set to False and add 'plugins' for production
        'password-file': os.path.join(os.getcwd(), "passwd") 
    },
    'topic-check': {
        'enabled': True,
        'plugins': ['topic_acl'],
    }
}

async def start_broker():
    broker = Broker(config)
    try:
        await broker.start()
        logger.info("MQTT Broker started successfully on port 1884")
        
        # Keep the broker running
        while True:
            await asyncio.sleep(3600)
            
    except Exception as e:
        logger.error(f"Broker failed: {e}")
    finally:
        await broker.shutdown()

if __name__ == '__main__':
    try:
        asyncio.run(start_broker())
    except KeyboardInterrupt:
        logger.info("Broker stopped by user")