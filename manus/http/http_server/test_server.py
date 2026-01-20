#!/usr/bin/env python3
"""
Test script for the HTTP/HTTPS server
Demonstrates all endpoints and features
"""

import requests
import json
import sys
from time import sleep

def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def print_response(response):
    """Print formatted response"""
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    try:
        print(f"Body: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Body: {response.text}")

def test_http_server(base_url="http://localhost:8000"):
    """Test HTTP server endpoints"""
    
    print_header("Testing HTTP Server")
    print(f"Base URL: {base_url}\n")
    
    # Test 1: Health Check
    print_header("Test 1: Health Check (GET /health)")
    try:
        response = requests.get(f"{base_url}/health")
        print_response(response)
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        print("✅ Health check passed")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    # Test 2: Server Info
    print_header("Test 2: Server Info (GET /api/info)")
    try:
        response = requests.get(f"{base_url}/api/info")
        print_response(response)
        assert response.status_code == 200
        assert "server" in response.json()
        print("✅ Server info passed")
    except Exception as e:
        print(f"❌ Server info failed: {e}")
        return False
    
    # Test 3: Valid Message
    print_header("Test 3: Valid Message (POST /api/message)")
    try:
        payload = {
            "message": "Hello, World!",
            "metadata": {
                "test": True,
                "timestamp": "2026-01-10"
            }
        }
        response = requests.post(
            f"{base_url}/api/message",
            json=payload
        )
        print_response(response)
        assert response.status_code == 201
        assert response.json()["success"] == True
        assert response.json()["echo"] == "Hello, World!"
        print("✅ Valid message passed")
    except Exception as e:
        print(f"❌ Valid message failed: {e}")
        return False
    
    # Test 4: Invalid Message (empty)
    print_header("Test 4: Invalid Message - Empty (POST /api/message)")
    try:
        payload = {"message": ""}
        response = requests.post(
            f"{base_url}/api/message",
            json=payload
        )
        print_response(response)
        assert response.status_code == 422  # Validation error
        print("✅ Invalid message validation passed")
    except Exception as e:
        print(f"❌ Invalid message validation failed: {e}")
        return False
    
    # Test 5: Invalid Message (missing field)
    print_header("Test 5: Invalid Message - Missing Field (POST /api/message)")
    try:
        payload = {"metadata": {"test": True}}
        response = requests.post(
            f"{base_url}/api/message",
            json=payload
        )
        print_response(response)
        assert response.status_code == 422  # Validation error
        print("✅ Missing field validation passed")
    except Exception as e:
        print(f"❌ Missing field validation failed: {e}")
        return False
    
    # Test 6: 404 Not Found
    print_header("Test 6: 404 Not Found (GET /nonexistent)")
    try:
        response = requests.get(f"{base_url}/nonexistent")
        print_response(response)
        assert response.status_code == 404
        print("✅ 404 handling passed")
    except Exception as e:
        print(f"❌ 404 handling failed: {e}")
        return False
    
    # Test 7: Root Endpoint
    print_header("Test 7: Root Endpoint (GET /)")
    try:
        response = requests.get(base_url)
        print(f"Status Code: {response.status_code}")
        print(f"Content Type: {response.headers.get('content-type')}")
        print(f"Body Length: {len(response.text)} bytes")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        print("✅ Root endpoint passed")
    except Exception as e:
        print(f"❌ Root endpoint failed: {e}")
        return False
    
    # Test 8: Response Headers
    print_header("Test 8: Response Headers (X-Process-Time)")
    try:
        response = requests.get(f"{base_url}/health")
        process_time = response.headers.get("X-Process-Time")
        print(f"X-Process-Time: {process_time}")
        assert process_time is not None
        assert float(process_time) > 0
        print("✅ Response headers passed")
    except Exception as e:
        print(f"❌ Response headers failed: {e}")
        return False
    
    print_header("All Tests Passed! ✅")
    return True

def test_https_server(base_url="https://localhost:8443"):
    """Test HTTPS server endpoints"""
    
    print_header("Testing HTTPS Server")
    print(f"Base URL: {base_url}\n")
    
    try:
        # Test with self-signed certificate (verify=False)
        response = requests.get(f"{base_url}/health", verify=False)
        print_response(response)
        assert response.status_code == 200
        print("✅ HTTPS server is working")
        return True
    except Exception as e:
        print(f"❌ HTTPS server test failed: {e}")
        print("Note: Make sure HTTPS server is running with:")
        print("  python3 server.py --https")
        return False

if __name__ == "__main__":
    # Parse command line arguments
    mode = sys.argv[1] if len(sys.argv) > 1 else "http"
    
    if mode == "http":
        success = test_http_server()
    elif mode == "https":
        success = test_https_server()
    else:
        print(f"Unknown mode: {mode}")
        print("Usage: python3 test_server.py [http|https]")
        sys.exit(1)
    
    sys.exit(0 if success else 1)
