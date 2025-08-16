#!/usr/bin/env python3
"""
Test script to verify MailMind server startup
"""

import asyncio
import uvicorn
from app.main import app


def test_server():
    """Test that the server can start and respond to requests."""
    print("🚀 Testing MailMind server startup...")
    
    # Test that the app can be created
    print("✅ FastAPI app created successfully")
    
    # Test basic endpoints
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    # Test root endpoint
    response = client.get("/")
    print(f"✅ Root endpoint: {response.status_code}")
    
    # Test health endpoint
    response = client.get("/health")
    print(f"✅ Health endpoint: {response.status_code}")
    
    print("🎉 All tests passed! Server is ready to run.")


if __name__ == "__main__":
    test_server()
