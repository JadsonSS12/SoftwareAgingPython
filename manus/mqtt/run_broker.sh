#!/bin/bash
# Production-grade runner for the MQTT broker

# Set environment variables if needed
export PYTHONPATH=$PYTHONPATH:.

# Start the broker
echo "Starting MQTT Broker..."
python3 broker.py
