# Robust Python MQTT Broker

This project implements a production-grade MQTT broker using Python 3.8 and the `aMQTT` framework.

## Features
- **Asyncio-native**: Built on Python's asyncio for high performance and scalability.
- **MQTT 3.1.1 Compliant**: Supports the standard MQTT protocol.
- **Dual Listeners**: Supports both standard TCP (port 1883) and WebSockets (port 8080).
- **Configurable**: Easily customizable via `config.yaml`.
- **Production Ready**: Includes a Dockerfile for containerized deployment.

## Installation

1. Install dependencies:
   ```bash
   pip install amqtt pyyaml
   ```

2. Run the broker:
   ```bash
   ./run_broker.sh
   ```

## Configuration
The broker is configured via `config.yaml`. You can adjust listeners, authentication, and logging settings there.

## Docker Deployment
To run using Docker:
```bash
docker build -t python-mqtt-broker .
docker run -p 1883:1883 -p 8080:8080 python-mqtt-broker
```
