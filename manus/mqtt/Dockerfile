# Use Python 3.8 slim image for a small footprint
FROM python:3.8-slim

# Set working directory
WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir amqtt pyyaml

# Copy application code
COPY . .

# Expose MQTT and WebSocket ports
EXPOSE 1883 8080

# Run the broker
CMD ["python", "broker.py"]
