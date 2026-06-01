"""
Dashboard routes for displaying summary and statistics.
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import (
    PreProduction, OnProduction, PostProduction, Checklist,
    MonthlyFinancialReport, ThreeMonthsClientFollowup, UpcomingClientsShoot,
    ClientsEditing, CameraRent, InvestmentToGrowCompany
)
from datetime import datetime, timedelta, date
import os

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

# Setup templates
template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
templates = Jinja2Templates(directory=template_dir)


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """
    Display main dashboard with comprehensive statistics.
    """
    try:
        # Service Steps Mechanism Statistics
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
        today = date.today()
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
        
        # ============================================
        # FINANCIAL DATA STATISTICS
        # ============================================
        
        # Monthly Financial Reports
        total_revenue = db.query(func.sum(MonthlyFinancialReport.total_amount)).scalar() or 0.0
        total_paid = db.query(func.sum(MonthlyFinancialReport.paid_amount)).scalar() or 0.0
        total_pending = db.query(func.sum(MonthlyFinancialReport.pending_amount)).scalar() or 0.0
        total_expenses = db.query(func.sum(MonthlyFinancialReport.expenses)).scalar() or 0.0
        total_profit = db.query(func.sum(MonthlyFinancialReport.profit)).scalar() or 0.0
        
        # Lead Statistics (Client Follow-up)
        three_months_ago = today - timedelta(days=90)
        total_leads = db.query(ThreeMonthsClientFollowup).filter(
            ThreeMonthsClientFollowup.date >= three_months_ago
        ).count()
        converted_leads = db.query(ThreeMonthsClientFollowup).filter(
            ThreeMonthsClientFollowup.date >= three_months_ago,
            ThreeMonthsClientFollowup.status == "Done"
        ).count()
        conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
        
        # Upcoming Shoots
        upcoming_shoots = db.query(UpcomingClientsShoot).filter(
            UpcomingClientsShoot.event_date >= today
        ).count()
        confirmed_shoots = db.query(UpcomingClientsShoot).filter(
            UpcomingClientsShoot.event_date >= today,
            UpcomingClientsShoot.confirmation == True
        ).count()
        
        # Editing Workload
        editing_projects_done = db.query(ClientsEditing).filter(
            ClientsEditing.work_status == "Done"
        ).count()
        editing_projects_pending = db.query(ClientsEditing).filter(
            ClientsEditing.work_status == "Pending"
        ).count()
        editing_revenue = db.query(func.sum(ClientsEditing.total_amount)).scalar() or 0.0
        
        # Camera Rent
        camera_rent_income = db.query(func.sum(CameraRent.total_amount)).scalar() or 0.0
        total_rent_days = db.query(func.sum(CameraRent.days)).scalar() or 0
        
        # Investment
        total_investment = db.query(func.sum(InvestmentToGrowCompany.amount)).scalar() or 0.0
        
        context = {
            "request": request,
            "page_title": "Dashboard",
            # Service Steps
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
            # Financial Data
            "total_revenue": total_revenue,
            "total_paid": total_paid,
            "total_pending": total_pending,
            "total_expenses": total_expenses,
            "total_profit": total_profit,
            "total_leads": total_leads,
            "converted_leads": converted_leads,
            "conversion_rate": round(conversion_rate, 2),
            "upcoming_shoots": upcoming_shoots,
            "confirmed_shoots": confirmed_shoots,
            "editing_done": editing_projects_done,
            "editing_pending": editing_projects_pending,
            "editing_revenue": editing_revenue,
            "camera_rent_income": camera_rent_income,
            "total_rent_days": total_rent_days,
            "total_investment": total_investment,
        }
        
        return templates.TemplateResponse("dashboard.html", context)
    
    except Exception as e:
        print(f"Error in dashboard: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": str(e)},
            status_code=500
        )
