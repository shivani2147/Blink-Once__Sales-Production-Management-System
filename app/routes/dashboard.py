"""
Dashboard routes for displaying summary and statistics.
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import PreProduction, OnProduction, PostProduction, Checklist
from datetime import datetime, timedelta
import os

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

# Setup templates
template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
templates = Jinja2Templates(directory=template_dir)


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """
    Display main dashboard with summary statistics.
    """
    try:
        # Get statistics from database
        pre_prod_count = db.query(PreProduction).count()
        on_prod_count = db.query(OnProduction).count()
        post_prod_count = db.query(PostProduction).count()
        checklist_count = db.query(Checklist).count()
        
        # Get pending tasks
        pending_pre_prod = db.query(PreProduction).filter(
            PreProduction.whatsapp_group == False
        ).count()
        pending_post_prod = db.query(PostProduction).filter(
            PostProduction.closure_date == None
        ).count()
        
        # Get upcoming events (next 7 days)
        today = datetime.now().date()
        week_end = today + timedelta(days=7)
        upcoming_events = db.query(PreProduction).filter(
            (PreProduction.event_date >= today) & (PreProduction.event_date <= week_end)
        ).count()
        
        # Get recent pre-production records
        recent_pre_prod = db.query(PreProduction).order_by(
            PreProduction.created_at.desc()
        ).limit(5).all()
        
        # Get overdue post-production tasks
        overdue_post_prod = []
        all_post_prod = db.query(PostProduction).filter(
            PostProduction.closure_date == None
        ).all()
        for task in all_post_prod:
            if task.is_overdue():
                overdue_post_prod.append(task)
        
        context = {
            "request": request,
            "page_title": "Dashboard",
            "pre_prod_total": pre_prod_count,
            "on_prod_total": on_prod_count,
            "post_prod_total": post_prod_count,
            "checklist_total": checklist_count,
            "pending_pre_prod": pending_pre_prod,
            "pending_post_prod": pending_post_prod,
            "upcoming_events": upcoming_events,
            "overdue_tasks": len(overdue_post_prod),
            "recent_records": recent_pre_prod,
            "overdue_post_prod": overdue_post_prod[:5],
        }
        
        return templates.TemplateResponse("dashboard.html", context)
    
    except Exception as e:
        print(f"Error in dashboard: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": str(e)},
            status_code=500
        )
