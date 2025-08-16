#!/usr/bin/env python3
"""
MailMind Startup Script

This script starts the MailMind FastAPI application with proper configuration.
"""

import os
import sys
import uvicorn
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings


def main():
    """Start the MailMind application."""
    print("🚀 Starting MailMind...")
    print(f"📊 Environment: {'Development' if settings.debug else 'Production'}")
    print(f"🗄️  Database: {settings.database_url}")
    print(f"🔗 API Documentation: http://localhost:8000/docs")
    print(f"📈 ReDoc Documentation: http://localhost:8000/redoc")
    print("-" * 50)
    
    # Run the application
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=True
    )


if __name__ == "__main__":
    main()
