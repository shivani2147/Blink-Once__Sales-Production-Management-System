"""
Dashboard routes for displaying summary and statistics.
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from app.database import get_db
from app.models import (
    PreProduction, OnProduction, PostProduction, Checklist, 
    MonthlyFinancialReport, ThreeMonthsClientFollowup, UpcomingClientsShoot,
    ClientsEditing, CameraRent, InvestmentToGrowCompany
)
from datetime import datetime, timedelta, date, time
import os
import calendar
from .monthly_financial import number_to_words

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

# Setup templates
template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
templates = Jinja2Templates(directory=template_dir)


@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    year: str = None,
    month: str = None
):
    """
    Display main dashboard with comprehensive statistics.
    """
    try:
        today = date.today()

        # ============================================
        # 0. DYNAMIC FILTERS DATA POPULATION
        # ============================================
        # Retrieve unique years present in the database to build filter options dynamically
        years_set = set()
        for y in db.query(MonthlyFinancialReport.year).distinct().all():
            if y[0]:
                years_set.add(int(y[0]))
        for d in db.query(extract('year', ThreeMonthsClientFollowup.date)).distinct().all():
            if d[0]:
                years_set.add(int(d[0]))
        for d in db.query(extract('year', PreProduction.created_at)).distinct().all():
            if d[0]:
                years_set.add(int(d[0]))

        # Include current year and previous year as default fallbacks
        current_year = today.year
        years_set.add(current_year)
        years_set.add(current_year - 1)
        years_list = sorted(list(years_set), reverse=True)

        # Standard months mapping list
        months_list = [(i, calendar.month_name[i]) for i in range(1, 13)]

        # Get values or set defaults
        selected_year = year if year else str(current_year)
        selected_month = month if month else "all"

        y_filter_val = None
        if selected_year != "all":
            try:
                y_filter_val = int(selected_year)
            except ValueError:
                pass

        m_filter_val = None
        if selected_month != "all":
            try:
                m_filter_val = int(selected_month)
            except ValueError:
                pass

        weeks_list = []

        start_date = None
        end_date = None
        if y_filter_val:
            if m_filter_val:
                start_date = date(y_filter_val, m_filter_val, 1)
                last_day = calendar.monthrange(y_filter_val, m_filter_val)[1]
                end_date = date(y_filter_val, m_filter_val, last_day)
            else:
                start_date = date(y_filter_val, 1, 1)
                end_date = date(y_filter_val, 12, 31)

        # Helper function to apply year/month/week filter on any Date/DateTime column
        def filter_q(query, col, is_datetime=False):
            if start_date and end_date:
                if is_datetime:
                    s_dt = datetime.combine(start_date, time.min)
                    e_dt = datetime.combine(end_date, time.max)
                    return query.filter(col >= s_dt, col <= e_dt)
                else:
                    return query.filter(col >= start_date, col <= end_date)

            # Fallback for individual filters (e.g. month selected without year, or others)
            if y_filter_val:
                query = query.filter(extract('year', col) == y_filter_val)
            if m_filter_val:
                query = query.filter(extract('month', col) == m_filter_val)
            return query

        # Helper function for Production modules using new year/month columns
        def filter_prod(query, model):
            if y_filter_val:
                query = query.filter(model.year == y_filter_val)
            if m_filter_val:
                query = query.filter(model.month == calendar.month_name[m_filter_val])
            return query

        # ============================================
        # 1. CLIENT & PROJECT STATS
        # ============================================
        clients_pre = {c[0] for c in filter_prod(db.query(PreProduction.couple_name), PreProduction).distinct().all() if c[0]}
        clients_on = {c[0] for c in filter_prod(db.query(OnProduction.couple_name), OnProduction).distinct().all() if c[0]}
        clients_post = {c[0] for c in filter_prod(db.query(PostProduction.couple_name), PostProduction).distinct().all() if c[0]}
        
        # MonthlyFinancialReport is month-year based and doesn't use standard filter_q directly
        m_query = db.query(MonthlyFinancialReport)
        if y_filter_val:
            m_query = m_query.filter(MonthlyFinancialReport.year == y_filter_val)
        if m_filter_val:
            m_query = m_query.filter(MonthlyFinancialReport.month == calendar.month_name[m_filter_val])
        monthly_reports = m_query.all()

        # Week filter removed


        clients_monthly = {r.client_name for r in monthly_reports if r.client_name}
        
        clients_followup = {c[0] for c in filter_q(db.query(ThreeMonthsClientFollowup.client_name), ThreeMonthsClientFollowup.date).distinct().all() if c[0]}
        clients_shoot = {c[0] for c in filter_q(db.query(UpcomingClientsShoot.client_name), UpcomingClientsShoot.date).distinct().all() if c[0]}
        clients_editing = {c[0] for c in filter_q(db.query(ClientsEditing.client_name), ClientsEditing.date).distinct().all() if c[0]}
        clients_rent = {c[0] for c in filter_q(db.query(CameraRent.client_name), CameraRent.date).distinct().all() if c[0]}
        
        all_client_names_set = clients_pre | clients_on | clients_post | clients_monthly | clients_followup | clients_shoot | clients_editing | clients_rent
        total_clients = len(all_client_names_set)
        all_client_names = sorted(all_client_names_set)

        # Unfiltered: fetch ALL distinct client names across every module for the modal popup
        _all_names: set = set()
        for c in db.query(PreProduction.couple_name).distinct().all():
            if c[0]: _all_names.add(c[0])
        for c in db.query(OnProduction.couple_name).distinct().all():
            if c[0]: _all_names.add(c[0])
        for c in db.query(PostProduction.couple_name).distinct().all():
            if c[0]: _all_names.add(c[0])
        for c in db.query(MonthlyFinancialReport.client_name).distinct().all():
            if c[0]: _all_names.add(c[0])
        for c in db.query(ThreeMonthsClientFollowup.client_name).distinct().all():
            if c[0]: _all_names.add(c[0])
        for c in db.query(UpcomingClientsShoot.client_name).distinct().all():
            if c[0]: _all_names.add(c[0])
        for c in db.query(ClientsEditing.client_name).distinct().all():
            if c[0]: _all_names.add(c[0])
        for c in db.query(CameraRent.client_name).distinct().all():
            if c[0]: _all_names.add(c[0])
        all_client_names_modal = sorted(_all_names)
        
        pre_prod_total = filter_prod(db.query(PreProduction), PreProduction).count()
        on_prod_total = filter_prod(db.query(OnProduction), OnProduction).count()
        post_prod_total = filter_prod(db.query(PostProduction), PostProduction).count()
        checklist_total = filter_q(db.query(Checklist), Checklist.created_at, is_datetime=True).count()

        total_projects = pre_prod_total

        # Ongoing Projects: On-Production + Post-Production (Pending Closure)
        pending_post_prod_count = filter_prod(db.query(PostProduction), PostProduction).filter(PostProduction.closure_date == None).count()
        ongoing_projects = on_prod_total + pending_post_prod_count

        # Completed Projects: Post-Production with closure date
        completed_projects = filter_prod(db.query(PostProduction), PostProduction).filter(PostProduction.closure_date != None).count()

        # Dynamic Incomplete Tasks calculation (on filtered records)
        pending_tasks = 0
        pre_prod_records = filter_prod(db.query(PreProduction), PreProduction).all()
        for p in pre_prod_records:
            fields = [p.advance_retainer_received, p.welcome_call, p.team_booking, p.story_designing_call, p.heartfelt_email_cra, p.terms_confirmation_cra, p.invoicing_cra, p.sending_jd_to_team, p.music_choice_link_cra, p.invitation_video, p.whatsapp_group]
            pending_tasks += sum(1 for f in fields if not f)

        on_prod_records = filter_prod(db.query(OnProduction), OnProduction).all()
        for o in on_prod_records:
            fields = [o.client_review, o.payment_received, o.bts_shoot, o.hospitality_gesture, o.story_designing_sheet_refer, o.checklist_shared_with_team]
            pending_tasks += sum(1 for f in fields if not f)

        post_prod_records = filter_prod(db.query(PostProduction), PostProduction).all()
        for p in post_prod_records:
            fields = [p.data_copy, p.best_couple_edits_3_days, p.all_raw_images, p.save_the_date, p.invite, p.countdown, p.celebrity_ai_reel, p.one_teaser, p.one_film, p.one_reel, p.full_length_film, p.edited_images_selection, p.edited_images_delivered, p.poster, p.albums_picture_selection, p.photobook_delivered, p.digital_portfolio_album, p.payment_recovery]
            pending_tasks += sum(1 for f in fields if not f)

        checklist_records = filter_q(db.query(Checklist), Checklist.created_at, is_datetime=True).all()
        for c in checklist_records:
            fields = [c.equipments_ready, c.traditional_videographer, c.traditional_photographer, c.candid_photographer, c.cinematographer, c.drone_shooter, c.pre_wedding_shoot]
            pending_tasks += sum(1 for f in fields if not f)

        # ============================================
        # 2. FINANCIAL DATA STATISTICS
        # ============================================
        # Use paid_amount from MonthlyFinancialReport so dashboard Total Revenue matches the Monthly Financial Reports page
        rev_monthly = sum(float(r.paid_amount or 0.0) for r in monthly_reports)
        
        # Only include confirmed/received amounts (work_status == 'Done') for sub-service revenue
        editing_records_done = filter_q(db.query(ClientsEditing), ClientsEditing.date).filter(ClientsEditing.work_status == "Done").all()
        rev_editing = sum(r.total_amount for r in editing_records_done)

        camera_records_done = filter_q(db.query(CameraRent), CameraRent.date).filter(CameraRent.work_status == "Done").all()
        rev_camera = sum(r.total_amount for r in camera_records_done)

        followup_records = filter_q(db.query(ThreeMonthsClientFollowup), ThreeMonthsClientFollowup.date).all()
        rev_followup = sum(r.total_amount for r in followup_records)

        shoot_records = filter_q(db.query(UpcomingClientsShoot), UpcomingClientsShoot.date).all()
        rev_shoots = sum(r.total_amount for r in shoot_records)

        # Exclude client follow-up revenue from the dashboard Total Revenue summary
        total_revenue = float(rev_monthly) + float(rev_editing) + float(rev_camera) + float(rev_shoots)
        exp_monthly = sum(r.expenses for r in monthly_reports)
        freelancer_expenses = sum(r.freelancer_amount for r in monthly_reports)

        investment_records = filter_q(db.query(InvestmentToGrowCompany), InvestmentToGrowCompany.date).all()
        total_investment = sum(r.total_amount for r in investment_records)
        
        total_expenses = float(exp_monthly) + float(freelancer_expenses) + float(total_investment)
        total_profit = total_revenue - total_expenses
        outflow_total = float(freelancer_expenses) + float(total_investment)
        
        # Calculate receivables/collections: Monthly Financial + Clients Editing + Camera Rent
        monthly_pending = sum(r.pending_amount for r in monthly_reports)

        editing_pending_records = filter_q(db.query(ClientsEditing), ClientsEditing.date).all()
        editing_pending = sum(r.pending_amount for r in editing_pending_records)

        camera_pending_records = filter_q(db.query(CameraRent), CameraRent.date).all()
        camera_pending = sum(r.pending_amount for r in camera_pending_records)
        
        pending_payments = float(monthly_pending) + float(editing_pending) + float(camera_pending)
        
        # Payment Recovery count from Post-Production where payment_recovery is False
        payment_recovery_pending = sum(1 for p in post_prod_records if p.payment_recovery == False)
        payment_recovery_done = sum(1 for p in post_prod_records if p.payment_recovery == True)

        camera_rent_income = float(rev_camera)
        editing_revenue = float(rev_editing)
        sub_service_revenue = camera_rent_income + editing_revenue

        # Calculate Cash & Online payments
        all_editing_records = filter_q(db.query(ClientsEditing), ClientsEditing.date).all()
        all_camera_records = filter_q(db.query(CameraRent), CameraRent.date).all()

        cash_monthly = sum(float(r.paid_amount or 0.0) for r in monthly_reports if r.payment_status == "Cash")
        cash_editing = sum(float(r.paid_amount or 0.0) for r in all_editing_records if r.payment_status == "Cash")
        cash_camera = sum(float(r.paid_amount or 0.0) for r in all_camera_records if r.payment_status == "Cash")
        total_cash = cash_monthly + cash_editing + cash_camera

        online_monthly = sum(float(r.paid_amount or 0.0) for r in monthly_reports if r.payment_status == "Online")
        online_editing = sum(float(r.paid_amount or 0.0) for r in all_editing_records if r.payment_status == "Online")
        online_camera = sum(float(r.paid_amount or 0.0) for r in all_camera_records if r.payment_status == "Online")
        total_online = online_monthly + online_editing + online_camera


        # ============================================
        # 3. LEADS & CONVERSION STATS
        # ============================================
        total_leads = len(followup_records)
        confirmed_clients = sum(1 for f in followup_records if f.status == "Done")
        rejected_leads = sum(1 for f in followup_records if f.status == "Rejected")
        quotations_sent = sum(1 for f in followup_records if f.status and "quotation sent" in f.status.lower())
        upcoming_followups = sum(1 for f in followup_records if f.status not in ["Done", "Rejected"])
        
        lead_conversion_rate = (confirmed_clients / total_leads * 100) if total_leads > 0 else 0.0

        # Upcoming Shoots
        upcoming_shoots_count = sum(1 for s in shoot_records if s.date >= today)

        # ============================================
        # 4. SERVICE STEPS COMPLETION TRACKER (AVERAGES)
        # ============================================
        pre_prod_avg = sum(p.get_completion_percentage() for p in pre_prod_records) / len(pre_prod_records) if pre_prod_records else 0.0
        on_prod_avg = sum(o.get_completion_percentage() for o in on_prod_records) / len(on_prod_records) if on_prod_records else 0.0
        post_prod_avg = sum(p.get_completion_percentage() for p in post_prod_records) / len(post_prod_records) if post_prod_records else 0.0
        checklist_avg = sum(c.get_completion_percentage() for c in checklist_records) / len(checklist_records) if checklist_records else 0.0

        # ============================================
        # 5. CHARTS & TREND DATA
        # ============================================
        # Group monthly_reports in Python to keep synchronization between chart & list
        month_order = {
            "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
            "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12
        }

        if selected_year != "all" and selected_month != "all":
            # Day-wise trends for that month (Revenue, Expenses, Profit)
            y_val = int(selected_year)
            m_val = int(selected_month)
            last_day = calendar.monthrange(y_val, m_val)[1]
            
            monthly_labels = [f"{d}" for d in range(1, last_day + 1)]
            monthly_revenue_dataset = [0.0] * last_day
            monthly_expenses_dataset = [0.0] * last_day
            
            def parse_days(event_date_str, max_day):
                if not event_date_str:
                    return [1]
                parts = [p.strip() for p in event_date_str.split(',')]
                days = []
                for p in parts:
                    if p.isdigit():
                        val = int(p)
                        if 1 <= val <= max_day:
                            days.append(val)
                    elif '-' in p:
                        try:
                            val = datetime.strptime(p, "%Y-%m-%d").day
                            if 1 <= val <= max_day:
                                days.append(val)
                        except ValueError:
                            pass
                return days if days else [1]

            # 1. Monthly Financial Reports
            for r in monthly_reports:
                days = parse_days(r.event_date, last_day)
                num_days_listed = len(days)
                rev_share = float(r.total_amount or 0.0) / num_days_listed
                exp_share = float((r.expenses or 0.0) + (r.freelancer_amount or 0.0)) / num_days_listed
                for day in days:
                    monthly_revenue_dataset[day - 1] += rev_share
                    monthly_expenses_dataset[day - 1] += exp_share

            # 2. Clients Editing
            for r in editing_records_done:
                if r.date:
                    day = r.date.day
                    if 1 <= day <= last_day:
                        monthly_revenue_dataset[day - 1] += float(r.total_amount or 0.0)

            # 3. Camera Rent
            for r in camera_records_done:
                if r.date:
                    day = r.date.day
                    if 1 <= day <= last_day:
                        monthly_revenue_dataset[day - 1] += float(r.total_amount or 0.0)

            # 4. Three Months Client Followup
            for r in followup_records:
                if r.date:
                    day = r.date.day
                    if 1 <= day <= last_day:
                        monthly_revenue_dataset[day - 1] += float(r.total_amount or 0.0)

            # 5. Upcoming Clients Shoot
            for r in shoot_records:
                if r.date:
                    day = r.date.day
                    if 1 <= day <= last_day:
                        monthly_revenue_dataset[day - 1] += float(r.total_amount or 0.0)

            # 6. Investment to Grow Company
            for r in investment_records:
                if r.date:
                    day = r.date.day
                    if 1 <= day <= last_day:
                        monthly_expenses_dataset[day - 1] += float(r.total_amount or 0.0)

            monthly_profit_dataset = [monthly_revenue_dataset[i] - monthly_expenses_dataset[i] for i in range(last_day)]

        elif selected_year != "all" and selected_month == "all":
            # Month-wise trends for the selected Year
            monthly_labels = [calendar.month_name[m] for m in range(1, 13)]
            monthly_revenue_dataset = [0.0] * 12
            monthly_expenses_dataset = [0.0] * 12
            
            # 1. Monthly Financial Reports
            for r in monthly_reports:
                m_idx = month_order.get(r.month, 1) - 1
                monthly_revenue_dataset[m_idx] += float(r.total_amount or 0.0)
                monthly_expenses_dataset[m_idx] += float((r.expenses or 0.0) + (r.freelancer_amount or 0.0))

            # 2. Clients Editing
            for r in editing_records_done:
                if r.date:
                    m_idx = r.date.month - 1
                    monthly_revenue_dataset[m_idx] += float(r.total_amount or 0.0)

            # 3. Camera Rent
            for r in camera_records_done:
                if r.date:
                    m_idx = r.date.month - 1
                    monthly_revenue_dataset[m_idx] += float(r.total_amount or 0.0)

            # 4. Three Months Client Followup
            for r in followup_records:
                if r.date:
                    m_idx = r.date.month - 1
                    monthly_revenue_dataset[m_idx] += float(r.total_amount or 0.0)

            # 5. Upcoming Clients Shoot
            for r in shoot_records:
                if r.date:
                    m_idx = r.date.month - 1
                    monthly_revenue_dataset[m_idx] += float(r.total_amount or 0.0)

            # 6. Investment to Grow Company
            for r in investment_records:
                if r.date:
                    m_idx = r.date.month - 1
                    monthly_expenses_dataset[m_idx] += float(r.total_amount or 0.0)

            monthly_profit_dataset = [monthly_revenue_dataset[i] - monthly_expenses_dataset[i] for i in range(12)]

        else:
            # Year-wise trends across all available years
            sorted_years = sorted(list(years_list))
            year_to_idx = {yr: idx for idx, yr in enumerate(sorted_years)}
            num_years = len(sorted_years)
            
            monthly_labels = [str(yr) for yr in sorted_years]
            monthly_revenue_dataset = [0.0] * num_years
            monthly_expenses_dataset = [0.0] * num_years
            
            # 1. Monthly Financial Reports
            for r in monthly_reports:
                yr = r.year
                if yr in year_to_idx:
                    idx = year_to_idx[yr]
                    monthly_revenue_dataset[idx] += float(r.total_amount or 0.0)
                    monthly_expenses_dataset[idx] += float((r.expenses or 0.0) + (r.freelancer_amount or 0.0))

            # 2. Clients Editing
            for r in editing_records_done:
                if r.date:
                    yr = r.date.year
                    if yr in year_to_idx:
                        idx = year_to_idx[yr]
                        monthly_revenue_dataset[idx] += float(r.total_amount or 0.0)

            # 3. Camera Rent
            for r in camera_records_done:
                if r.date:
                    yr = r.date.year
                    if yr in year_to_idx:
                        idx = year_to_idx[yr]
                        monthly_revenue_dataset[idx] += float(r.total_amount or 0.0)

            # 4. Three Months Client Followup
            for r in followup_records:
                if r.date:
                    yr = r.date.year
                    if yr in year_to_idx:
                        idx = year_to_idx[yr]
                        monthly_revenue_dataset[idx] += float(r.total_amount or 0.0)

            # 5. Upcoming Clients Shoot
            for r in shoot_records:
                if r.date:
                    yr = r.date.year
                    if yr in year_to_idx:
                        idx = year_to_idx[yr]
                        monthly_revenue_dataset[idx] += float(r.total_amount or 0.0)

            # 6. Investment to Grow Company
            for r in investment_records:
                if r.date:
                    yr = r.date.year
                    if yr in year_to_idx:
                        idx = year_to_idx[yr]
                        monthly_expenses_dataset[idx] += float(r.total_amount or 0.0)

            monthly_profit_dataset = [monthly_revenue_dataset[i] - monthly_expenses_dataset[i] for i in range(num_years)]

        # Lead Status Chart
        lead_chart_data = {"Confirmed": 0, "Rejected": 0, "Pending": 0}
        for f in followup_records:
            if f.status == "Done":
                lead_chart_data["Confirmed"] += 1
            elif f.status == "Rejected":
                lead_chart_data["Rejected"] += 1
            else:
                lead_chart_data["Pending"] += 1

        # Platform Lead Sources Chart
        platform_lead_data = {"JD": 0, "Meta Ads": 0, "Word of Mouth": 0}
        for f in followup_records:
            plat = f.platform
            if plat in platform_lead_data:
                platform_lead_data[plat] += 1
            else:
                platform_lead_data[plat] = platform_lead_data.get(plat, 0) + 1

        # ============================================
        # 6. RECENT MODULE SUMMARIES & EVENT CALENDAR
        # ============================================
        recent_pre_prod = sorted(pre_prod_records, key=lambda x: x.created_at or datetime.min, reverse=True)[:5]
        recent_on_prod = sorted(on_prod_records, key=lambda x: x.created_at or datetime.min, reverse=True)[:5]
        recent_post_prod = sorted(post_prod_records, key=lambda x: x.created_at or datetime.min, reverse=True)[:5]
        recent_checklists = sorted(checklist_records, key=lambda x: x.created_at or datetime.min, reverse=True)[:5]
        recent_financials = sorted(monthly_reports, key=lambda x: (x.year or 0, month_order.get(x.month, 0)), reverse=True)[:5]
        recent_followups = sorted(followup_records, key=lambda x: x.date or date.min, reverse=True)[:5]

        # Overdue post production tasks
        overdue_post_prod = [task for task in post_prod_records if task.closure_date == None and task.is_overdue()]

        # Upcoming events (Next 30 days) from UpcomingClientsShoot
        upcoming_shoots_list = sorted([s for s in shoot_records if s.date >= today], key=lambda x: x.date)[:10]

        # Upcoming deadlines from PostProduction
        upcoming_deadlines_list = sorted([p for p in post_prod_records if p.deadline and p.deadline >= today], key=lambda x: x.deadline)[:10]

        context = {
            "request": request,
            "page_title": "Dashboard",
            # Filters dropdown parameters
            "years_list": years_list,
            "months_list": months_list,
            "years_list": years_list,
            "months_list": months_list,
            "selected_year": selected_year,
            "selected_month": selected_month,

            # KPI Widgets
            "total_clients": total_clients,
            "all_client_names": all_client_names,
            "all_client_names_modal": all_client_names_modal,
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
            "outflow_total": outflow_total,
            "outflow_total_words": number_to_words(outflow_total),
            "pending_payments": pending_payments,
            "pending_payments_words": number_to_words(pending_payments),
            "payment_recovery_pending": payment_recovery_pending,
            "payment_recovery_done": payment_recovery_done,
            "camera_rent_income": camera_rent_income,
            "camera_rent_income_words": number_to_words(camera_rent_income),
            "editing_revenue": editing_revenue,
            "editing_revenue_words": number_to_words(editing_revenue),
            "sub_service_revenue": sub_service_revenue,
            "sub_service_revenue_words": number_to_words(sub_service_revenue),
            "total_cash": total_cash,
            "total_cash_words": number_to_words(total_cash),
            "total_online": total_online,
            "total_online_words": number_to_words(total_online),
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
            "upcoming_deadlines_list": upcoming_deadlines_list,
            "today": today,

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
