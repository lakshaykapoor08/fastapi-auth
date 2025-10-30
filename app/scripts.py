"""
Command-line scripts for the FastAPI application
"""

import uvicorn
from app.config import get_settings

settings = get_settings()


def dev():
    """Run development server with hot reload"""
    uvicorn.run(
        "app.main:app", host="127.0.0.1", port=8000, reload=True, log_level="info"
    )


def start():
    """Run production server"""
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, workers=4, log_level="info")


def prod():
    """Run production server (alias for start)"""
    start()
