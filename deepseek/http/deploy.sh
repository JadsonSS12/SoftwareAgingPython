#!/bin/bash
# Deployment script for robust HTTP/HTTPS server

set -e

echo "🚀 Deploying Robust HTTP/HTTPS Server"

# Check Python version
python_version=$(python3 --version)
echo "📦 Python version: $python_version"

# Create virtual environment
echo "🔧 Setting up virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Generate SSL certificate if needed
if [ "$SSL_ENABLED" = "true" ] && [ ! -f "cert.pem" ]; then
    echo "🔐 Generating SSL certificate..."
    python generate_ssl_cert.py
fi

# Validate configuration
echo "🔍 Validating configuration..."
python -c "
import sys
sys.path.insert(0, '.')
from environment import ServerConfig
try:
    ServerConfig.validate_config()
    print('✅ Configuration is valid')
except ValueError as e:
    print(f'❌ {e}')
    sys.exit(1)
"

# Start the server
echo "🌐 Starting server..."
if [ "$ENVIRONMENT" = "production" ]; then
    # Production mode with multiple workers
    echo "🏭 Running in production mode with $WORKERS workers"
    uvicorn app:app \
        --host "$HOST" \
        --port "$PORT" \
        --workers "$WORKERS" \
        --ssl-certfile "${SSL_CERTFILE:-cert.pem}" \
        --ssl-keyfile "${SSL_KEYFILE:-key.pem}" \
        --access-log \
        --timeout-keep-alive 30
else
    # Development mode
    echo "🔧 Running in development mode"
    python app.py
fi