"""
ProductionFlow CRM - Main Application Entry Point
Professional Sales & Production Management System for Creative Production Companies

Server: BO-LAPTOP\SQLEXPRESS
Database: BlinkOnce__ProductionManagementSystem
"""

import secrets
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
try:
    from starlette.middleware.sessions import SessionMiddleware
except Exception as e:
    raise RuntimeError(
        "Missing dependency for session middleware. Install requirements: `pip install -r requirements.txt`. "
        f"Original error: {e}"
    )
import os

# Import configuration and database
from app.config import APP_TITLE, APP_VERSION, APP_DESCRIPTION, DEBUG, RELOAD, SECRET_KEY
from app.database import init_db

# Import route handlers
from app.routes import (
    dashboard, 
    pre_production, 
    on_production, 
    post_production, 
    monthly_financial,
    client_followup,
    investment,
    editing,
    camera_rent,
    upcoming_shoots,
    freelancers,
    performance_hub,
    auth
)

# Create FastAPI application
app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Ensure CSRF token is present in session for templates and form validation
@app.middleware("http")
async def ensure_csrf_token_middleware(request, call_next):
    """Ensure a CSRF token exists in the user's session for form protection."""
    try:
        if request.session.get("csrf_token") is None:
            request.session["csrf_token"] = secrets.token_urlsafe(32)
    except Exception:
        # If sessions are unavailable for some reason, continue without failing here.
        pass
    response = await call_next(request)
    return response

@app.middleware("http")
async def require_auth_middleware(request, call_next):
    """Ensure user is authenticated for protected routes."""
    path = request.url.path
    # Allow static files, auth endpoints, and docs to be public
    if path.startswith("/static") or path.startswith("/api/") or path.startswith("/openapi.json") or path in ["/login", "/logout", "/health"]:
        return await call_next(request)
    
    # Check if user is authenticated
    if not request.session.get("user"):
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/login", status_code=303)
        
    return await call_next(request)

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "app", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include routers
app.include_router(dashboard.router)
app.include_router(pre_production.router)
app.include_router(on_production.router)
app.include_router(post_production.router)
# app.include_router(checklist.router)  # Checklist management removed

# Include financial data routers
app.include_router(monthly_financial.router)
app.include_router(client_followup.router)
app.include_router(investment.router)
app.include_router(editing.router)
app.include_router(camera_rent.router)
app.include_router(upcoming_shoots.router)
app.include_router(freelancers.router)
app.include_router(performance_hub.router)
app.include_router(auth.router)


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
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=RELOAD,
        log_level="info"
    )
  