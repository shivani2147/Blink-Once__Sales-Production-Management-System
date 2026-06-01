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
from .monthly_financial import number_to_words

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
        today = date.today()

        # ============================================
        # 1. CLIENT & PROJECT STATS
        # ============================================
        clients_pre = {c[0] for c in db.query(PreProduction.couple_name).distinct().all() if c[0]}
        clients_on = {c[0] for c in db.query(OnProduction.couple_name).distinct().all() if c[0]}
        clients_post = {c[0] for c in db.query(PostProduction.couple_name).distinct().all() if c[0]}
        clients_monthly = {c[0] for c in db.query(MonthlyFinancialReport.client_name).distinct().all() if c[0]}
        clients_followup = {c[0] for c in db.query(ThreeMonthsClientFollowup.client_name).distinct().all() if c[0]}
        clients_shoot = {c[0] for c in db.query(UpcomingClientsShoot.client_name).distinct().all() if c[0]}
        clients_editing = {c[0] for c in db.query(ClientsEditing.client_name).distinct().all() if c[0]}
        clients_rent = {c[0] for c in db.query(CameraRent.client_name).distinct().all() if c[0]}
        
        total_clients = len(clients_pre | clients_on | clients_post | clients_monthly | clients_followup | clients_shoot | clients_editing | clients_rent)
        
        pre_prod_total = db.query(PreProduction).count()
        on_prod_total = db.query(OnProduction).count()
        post_prod_total = db.query(PostProduction).count()
        checklist_total = db.query(Checklist).count()

        total_projects = pre_prod_total

        # Ongoing Projects: On-Production + Post-Production (Pending Closure)
        pending_post_prod_count = db.query(PostProduction).filter(PostProduction.closure_date == None).count()
        ongoing_projects = on_prod_total + pending_post_prod_count

        # Completed Projects: Post-Production with closure date
        completed_projects = db.query(PostProduction).filter(PostProduction.closure_date != None).count()

        # Dynamic Incomplete Tasks calculation
        pending_tasks = 0
        for p in db.query(PreProduction).all():
            fields = [p.advance_retainer_received, p.welcome_call, p.team_booking, p.story_designing_call, p.heartfelt_email_cra, p.terms_confirmation_cra, p.invoicing_cra, p.sending_jd_to_team, p.music_choice_link_cra, p.invitation_video, p.whatsapp_group]
            pending_tasks += sum(1 for f in fields if not f)
        for o in db.query(OnProduction).all():
            fields = [o.client_review, o.payment_received, o.bts_shoot, o.hospitality_gesture, o.story_designing_sheet_refer, o.checklist_shared_with_team]
            pending_tasks += sum(1 for f in fields if not f)
        for p in db.query(PostProduction).all():
            fields = [p.data_copy, p.best_couple_edits_3_days, p.all_raw_images, p.save_the_date, p.invite, p.countdown, p.celebrity_ai_reel, p.one_teaser, p.one_film, p.one_reel, p.full_length_film, p.edited_images_selection, p.edited_images_delivered, p.poster, p.albums_picture_selection, p.photobook_delivered, p.digital_portfolio_album, p.payment_recovery]
            pending_tasks += sum(1 for f in fields if not f)
        for c in db.query(Checklist).all():
            fields = [c.equipments_ready, c.traditional_videographer, c.traditional_photographer, c.candid_photographer, c.cinematographer, c.drone_shooter, c.pre_wedding_shoot]
            pending_tasks += sum(1 for f in fields if not f)

        # ============================================
        # 2. FINANCIAL DATA STATISTICS
        # ============================================
        rev_monthly = db.query(func.sum(MonthlyFinancialReport.total_amount)).scalar() or 0.0
        rev_editing = db.query(func.sum(ClientsEditing.total_amount)).scalar() or 0.0
        rev_camera = db.query(func.sum(CameraRent.total_amount)).scalar() or 0.0
        total_revenue = float(rev_monthly) + float(rev_editing) + float(rev_camera)

        exp_monthly = db.query(func.sum(MonthlyFinancialReport.expenses)).scalar() or 0.0
        freelancer_expenses = db.query(func.sum(MonthlyFinancialReport.freelancer_amount)).scalar() or 0.0
        total_investment = db.query(func.sum(InvestmentToGrowCompany.amount)).scalar() or 0.0
        total_expenses = float(exp_monthly) + float(freelancer_expenses) + float(total_investment)

        total_profit = total_revenue - total_expenses
        pending_payments = db.query(func.sum(MonthlyFinancialReport.pending_amount)).scalar() or 0.0
        
        # Payment Recovery count from Post-Production where payment_recovery is False
        payment_recovery_pending = db.query(PostProduction).filter(PostProduction.payment_recovery == False).count()
        payment_recovery_done = db.query(PostProduction).filter(PostProduction.payment_recovery == True).count()

        camera_rent_income = float(rev_camera)
        editing_revenue = float(rev_editing)

        # ============================================
        # 3. LEADS & CONVERSION STATS
        # ============================================
        total_leads = db.query(ThreeMonthsClientFollowup).count()
        confirmed_clients = db.query(ThreeMonthsClientFollowup).filter(ThreeMonthsClientFollowup.status == "Done").count()
        rejected_leads = db.query(ThreeMonthsClientFollowup).filter(ThreeMonthsClientFollowup.status == "Rejected").count()
        quotations_sent = db.query(ThreeMonthsClientFollowup).filter(ThreeMonthsClientFollowup.status.ilike("%quotation sent%")).count()
        upcoming_followups = db.query(ThreeMonthsClientFollowup).filter(
            ~ThreeMonthsClientFollowup.status.in_(["Done", "Rejected"])
        ).count()
        
        lead_conversion_rate = (confirmed_clients / total_leads * 100) if total_leads > 0 else 0.0

        # Upcoming Shoots
        upcoming_shoots_count = db.query(UpcomingClientsShoot).filter(UpcomingClientsShoot.date >= today).count()

        # ============================================
        # 4. SERVICE STEPS COMPLETION TRACKER (AVERAGES)
        # ============================================
        pre_prod_records = db.query(PreProduction).all()
        pre_prod_avg = sum(p.get_completion_percentage() for p in pre_prod_records) / len(pre_prod_records) if pre_prod_records else 0.0

        on_prod_records = db.query(OnProduction).all()
        on_prod_avg = sum(o.get_completion_percentage() for o in on_prod_records) / len(on_prod_records) if on_prod_records else 0.0

        post_prod_records = db.query(PostProduction).all()
        post_prod_avg = sum(p.get_completion_percentage() for p in post_prod_records) / len(post_prod_records) if post_prod_records else 0.0

        checklist_records = db.query(Checklist).all()
        checklist_avg = sum(c.get_completion_percentage() for c in checklist_records) / len(checklist_records) if checklist_records else 0.0

        # ============================================
        # 5. CHARTS & TREND DATA
        # ============================================
        # Monthly Revenue Trend, Profit vs Expense, Business Growth (Profit)
        monthly_financial_data = db.query(
            MonthlyFinancialReport.year,
            MonthlyFinancialReport.month,
            func.sum(MonthlyFinancialReport.total_amount).label('revenue'),
            func.sum(MonthlyFinancialReport.expenses + MonthlyFinancialReport.freelancer_amount).label('expenses'),
            func.sum(MonthlyFinancialReport.profit).label('profit')
        ).group_by(MonthlyFinancialReport.year, MonthlyFinancialReport.month).all()

        month_order = {
            "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
            "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12
        }
        
        sorted_monthly = sorted(
            monthly_financial_data,
            key=lambda x: (x[0] or 0, month_order.get(x[1], 0))
        )

        monthly_labels = [f"{x[1]} {x[0]}" for x in sorted_monthly]
        monthly_revenue_dataset = [float(x[2] or 0.0) for x in sorted_monthly]
        monthly_expenses_dataset = [float(x[3] or 0.0) for x in sorted_monthly]
        monthly_profit_dataset = [float(x[4] or 0.0) for x in sorted_monthly]

        # Lead Status Chart
        lead_status_counts = db.query(
            ThreeMonthsClientFollowup.status,
            func.count(ThreeMonthsClientFollowup.id)
        ).group_by(ThreeMonthsClientFollowup.status).all()
        
        lead_chart_data = {"Confirmed": 0, "Rejected": 0, "Pending": 0}
        for status, count in lead_status_counts:
            if status == "Done":
                lead_chart_data["Confirmed"] += count
            elif status == "Rejected":
                lead_chart_data["Rejected"] += count
            else:
                lead_chart_data["Pending"] += count

        # Platform Lead Sources Chart
        platform_counts = db.query(
            ThreeMonthsClientFollowup.platform,
            func.count(ThreeMonthsClientFollowup.id)
        ).group_by(ThreeMonthsClientFollowup.platform).all()
        
        platform_lead_data = {"JD": 0, "Meta Ads": 0, "Word of Mouth": 0}
        for plat, count in platform_counts:
            if plat in platform_lead_data:
                platform_lead_data[plat] = count
            else:
                platform_lead_data[plat] = platform_lead_data.get(plat, 0) + count

        # ============================================
        # 6. RECENT MODULE SUMMARIES & EVENT CALENDAR
        # ============================================
        recent_pre_prod = db.query(PreProduction).order_by(PreProduction.created_at.desc()).limit(5).all()
        recent_on_prod = db.query(OnProduction).order_by(OnProduction.created_at.desc()).limit(5).all()
        recent_post_prod = db.query(PostProduction).order_by(PostProduction.created_at.desc()).limit(5).all()
        recent_checklists = db.query(Checklist).order_by(Checklist.created_at.desc()).limit(5).all()
        recent_financials = db.query(MonthlyFinancialReport).order_by(MonthlyFinancialReport.year.desc(), MonthlyFinancialReport.month.desc()).limit(5).all()
        recent_followups = db.query(ThreeMonthsClientFollowup).order_by(ThreeMonthsClientFollowup.date.desc()).limit(5).all()

        # Overdue post production tasks
        overdue_post_prod = [task for task in db.query(PostProduction).filter(PostProduction.closure_date == None).all() if task.is_overdue()]

        # Upcoming events (Next 30 days) from UpcomingClientsShoot and PreProduction
        upcoming_shoots_list = db.query(UpcomingClientsShoot).filter(
            UpcomingClientsShoot.date >= today
        ).order_by(UpcomingClientsShoot.date.asc()).limit(10).all()

        context = {
            "request": request,
            "page_title": "Dashboard",
            # KPI Widgets
            "total_clients": total_clients,
            "total_projects": total_projects,
            "upcoming_shoots_count": upcoming_shoots_count,
            "ongoing_projects": ongoing_projects,
            "completed_projects": completed_projects,
            "pending_tasks": pending_tasks,
            "total_revenue": total_revenue,
            "total_revenue_words": number_to_words(total_revenue),
            "total_expenses": total_expenses,
            "total_expenses_words": number_to_words(total_expenses),
            "total_profit": total_profit,
            "total_profit_words": number_to_words(total_profit),
            "total_investment": total_investment,
            "total_investment_words": number_to_words(total_investment),
            "freelancer_expenses": freelancer_expenses,
            "freelancer_expenses_words": number_to_words(freelancer_expenses),
            "pending_payments": pending_payments,
            "pending_payments_words": number_to_words(pending_payments),
            "payment_recovery_pending": payment_recovery_pending,
            "payment_recovery_done": payment_recovery_done,
            "camera_rent_income": camera_rent_income,
            "camera_rent_income_words": number_to_words(camera_rent_income),
            "editing_revenue": editing_revenue,
            "editing_revenue_words": number_to_words(editing_revenue),
            "lead_conversion_rate": round(lead_conversion_rate, 2),
            "total_leads": total_leads,
            "confirmed_clients": confirmed_clients,
            "rejected_leads": rejected_leads,
            "quotations_sent": quotations_sent,
            "upcoming_followups": upcoming_followups,
            
            # Module averages
            "pre_prod_total": pre_prod_total,
            "on_prod_total": on_prod_total,
            "post_prod_total": post_prod_total,
            "checklist_total": checklist_total,
            "pre_prod_avg": round(pre_prod_avg, 1),
            "on_prod_avg": round(on_prod_avg, 1),
            "post_prod_avg": round(post_prod_avg, 1),
            "checklist_avg": round(checklist_avg, 1),

            # Recent tables
            "recent_pre_prod": recent_pre_prod,
            "recent_on_prod": recent_on_prod,
            "recent_post_prod": recent_post_prod,
            "recent_checklists": recent_checklists,
            "recent_financials": recent_financials,
            "recent_followups": recent_followups,
            "overdue_post_prod": overdue_post_prod[:5],
            "overdue_tasks": len(overdue_post_prod),
            "upcoming_shoots_list": upcoming_shoots_list,

            # Chart datasets (JSON ready lists)
            "monthly_labels": monthly_labels,
            "monthly_revenue_dataset": monthly_revenue_dataset,
            "monthly_expenses_dataset": monthly_expenses_dataset,
            "monthly_profit_dataset": monthly_profit_dataset,
            "lead_chart_data": lead_chart_data,
            "platform_lead_data": platform_lead_data,
        }

        return templates.TemplateResponse("dashboard.html", context)

    except Exception as e:
        print(f"Error in dashboard: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": str(e)},
            status_code=500
        )
