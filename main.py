"""
ProductionFlow CRM - Main Application Entry Point
Professional Sales & Production Management System for Creative Production Companies

Server: BO-LAPTOP\SQLEXPRESS
Database: BlinkOnce__ProductionManagementSystem
"""

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

# Import configuration and database
from app.config import APP_TITLE, APP_VERSION, APP_DESCRIPTION, DEBUG, RELOAD
from app.database import init_db

# Import route handlers
from app.routes import dashboard, pre_production, on_production, post_production, checklist

# Create FastAPI application
app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "app", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include routers
app.include_router(dashboard.router)
app.include_router(pre_production.router)
app.include_router(on_production.router)
app.include_router(post_production.router)
app.include_router(checklist.router)


@app.on_event("startup")
async def startup_event():
    """Initialize database and create tables on startup."""
    print("🚀 Starting ProductionFlow CRM...")
    print(f"📊 Application: {APP_TITLE} v{APP_VERSION}")
    try:
        init_db()
        print("✓ Database initialized successfully")
    except Exception as e:
        print(f"⚠️  Database initialization warning: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    print("🛑 Shutting down ProductionFlow CRM...")


@app.get("/")
async def root():
    """Root endpoint - redirect to dashboard."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/dashboard/")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": APP_TITLE,
        "version": APP_VERSION
    }


if __name__ == "__main__":
    print(f"""
    ╔════════════════════════════════════════╗
    ║     ProductionFlow CRM                 ║
    ║   Sales & Production Management        ║
    ╚════════════════════════════════════════╝
    
    📌 Server: http://localhost:8000
    📚 API Docs: http://localhost:8000/api/docs
    📖 ReDoc: http://localhost:8000/api/redoc
    
    Press CTRL+C to stop the server
    """)
    
    # Run the application
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=RELOAD,
        log_level="info"
    )
  