"""
FastAPI application factory and initialization.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.config import APP_TITLE, APP_VERSION, APP_DESCRIPTION
import os

def create_app():
    """Create and configure FastAPI application."""
    app = FastAPI(
        title=APP_TITLE,
        version=APP_VERSION,
        description=APP_DESCRIPTION,
    )
    
    # Mount static files
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    return app
