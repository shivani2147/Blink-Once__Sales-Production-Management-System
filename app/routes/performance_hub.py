"""
Performance Hub routes for consolidating monthly and client-wise business summary.
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
    ClientsEditing, CameraRent, InvestmentToGrowCompany, FreelancerWork
)
from datetime import datetime, timedelta, date, time
import os
import calendar
from collections import defaultdict

router = APIRouter(prefix="/performance-hub", tags=["Performance Hub"])

# Setup templates
template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
templates = Jinja2Templates(directory=template_dir)


@router.get("/", response_class=HTMLResponse)
async def performance_hub(
    request: Request,
    db: Session = Depends(get_db),
    year: str = None,
    month: str = None
):
    """
    Display Monthly Performance Hub with consolidated month-wise and client-wise data.
    """
    try:
        today = date.today()

        # Build dynamic years
        years_set = set()
        for y in db.query(MonthlyFinancialReport.year).distinct().all():
            if y[0]: years_set.add(int(y[0]))
        for d in db.query(extract('year', ThreeMonthsClientFollowup.date)).distinct().all():
            if d[0]: years_set.add(int(d[0]))
        current_year = today.year
        years_set.add(current_year)
        years_set.add(current_year - 1)
        years_list = sorted(list(years_set), reverse=True)

        months_list = [(i, calendar.month_name[i]) for i in range(1, 13)]

        selected_year = year if year else str(current_year)
        selected_month = month if month else "all"

        # Helpers for month parsing
        def get_month_str(d):
            if isinstance(d, date) or isinstance(d, datetime):
                return f"{d.year}-{d.month:02d}"
            return None
        
        def month_name_to_num(name):
            try:
                return list(calendar.month_name).index(name)
            except ValueError:
                return 1

        # Fetch all required data
        pre_prods = db.query(PreProduction).all()
        on_prods = db.query(OnProduction).all()
        post_prods = db.query(PostProduction).all()
        monthly_reps = db.query(MonthlyFinancialReport).all()
        followups = db.query(ThreeMonthsClientFollowup).all()
        shoots = db.query(UpcomingClientsShoot).all()
        editings = db.query(ClientsEditing).all()
        camera_rents = db.query(CameraRent).all()
        investments = db.query(InvestmentToGrowCompany).all()

        # Monthly Aggregation Data Structure
        # Key: "YYYY-MM"
        monthly_stats = defaultdict(lambda: {
            "Total Revenue": 0.0,
            "Potential Revenue": 0.0,
            "Confirmed Revenue": 0.0,
            "Total Expenses": 0.0,
            "Freelancer Expenses": 0.0,
            "Total Investments": 0.0,
            "Total Profit": 0.0,
            "Total Leads": 0,
            "Confirmed Clients": 0,
            "Rejected Leads": 0,
            "Upcoming Shoots": 0,
            "Editing Revenue": 0.0,
            "Camera Rent Revenue": 0.0,
            "Pending Payments": 0.0,
            "Payment Recovery": 0,
            "Payment Recovery Pending": 0,
            "Pre-Production Projects": 0,
            "On-Production Projects": 0,
            "Post-Production Projects": 0,
            "Completed Projects": 0,
            "Ongoing Projects": 0,
        })

        # Client-wise Aggregation Data Structure
        # Key: "Client Name"
        client_stats = defaultdict(lambda: {
            "Client Name": "",
            "Event Type": "",
            "Event Date": "",
            "Total Revenue Generated": 0.0,
            "Total Expenses": 0.0,
            "Freelancer Cost": 0.0,
            "Profit Earned": 0.0,
            "Current Project Stage": "Unknown",
            "Payment Status": "Unknown",
            "Work Status": "Pending",
            "History": [],
            "Month": ""
        })

        # 1. Monthly Financial Reports
        for r in monthly_reps:
            m_key = f"{r.year}-{month_name_to_num(r.month):02d}"
            c_key = r.client_name
            
            # Month Stats
            monthly_stats[m_key]["Total Revenue"] += r.total_amount
            monthly_stats[m_key]["Confirmed Revenue"] += r.total_amount
            monthly_stats[m_key]["Total Expenses"] += r.expenses + r.freelancer_amount
            monthly_stats[m_key]["Freelancer Expenses"] += r.freelancer_amount
            monthly_stats[m_key]["Total Profit"] += r.profit
            monthly_stats[m_key]["Pending Payments"] += r.pending_amount

            # Client Stats
            client_stats[c_key]["Client Name"] = c_key
            client_stats[c_key]["Event Type"] = r.event_type or client_stats[c_key]["Event Type"]
            client_stats[c_key]["Event Date"] = r.event_date or client_stats[c_key]["Event Date"]
            client_stats[c_key]["Total Revenue Generated"] += r.total_amount
            client_stats[c_key]["Total Expenses"] += r.expenses
            client_stats[c_key]["Freelancer Cost"] += r.freelancer_amount
            client_stats[c_key]["Profit Earned"] += r.profit
            client_stats[c_key]["Payment Status"] = r.payment_status if r.pending_amount == 0 else "Pending"
            client_stats[c_key]["Work Status"] = r.work_status
            client_stats[c_key]["History"].append("Financial Report Logged")
            client_stats[c_key]["Month"] = m_key

        # 2. Followups
        for f in followups:
            if not f.date: continue
            m_key = get_month_str(f.date)
            c_key = f.client_name
            
            monthly_stats[m_key]["Total Leads"] += 1
            if f.status == "Done":
                monthly_stats[m_key]["Confirmed Clients"] += 1
                # If they are confirmed but not in financial reports yet, we add their total_amount
                # but let's assume they're generally captured in Financials.
            elif f.status == "Rejected":
                monthly_stats[m_key]["Rejected Leads"] += 1
            else:
                monthly_stats[m_key]["Potential Revenue"] += f.total_amount
            
            client_stats[c_key]["Client Name"] = c_key
            if not client_stats[c_key]["Event Type"]:
                client_stats[c_key]["Event Type"] = f.event_type
            if not client_stats[c_key]["Event Date"]:
                client_stats[c_key]["Event Date"] = f.event_date
            client_stats[c_key]["Month"] = m_key

        # 3. Shoots
        for s in shoots:
            if not s.date: continue
            m_key = get_month_str(s.date)
            c_key = s.client_name
            
            monthly_stats[m_key]["Upcoming Shoots"] += 1
            if s.status != "Done":
                monthly_stats[m_key]["Potential Revenue"] += s.total_amount
                
            client_stats[c_key]["Client Name"] = c_key

        # 4. Editing
        for e in editings:
            if not e.date: continue
            m_key = get_month_str(e.date)
            c_key = e.client_name
            
            monthly_stats[m_key]["Total Revenue"] += e.total_amount
            monthly_stats[m_key]["Editing Revenue"] += e.total_amount
            monthly_stats[m_key]["Pending Payments"] += e.pending_amount
            
            client_stats[c_key]["Client Name"] = c_key
            client_stats[c_key]["Total Revenue Generated"] += e.total_amount
            client_stats[c_key]["History"].append(f"Editing: {e.editing_type}")

        # 5. Camera Rent
        for c in camera_rents:
            if not c.date: continue
            m_key = get_month_str(c.date)
            c_key = c.client_name
            
            monthly_stats[m_key]["Total Revenue"] += float(c.total_amount)
            monthly_stats[m_key]["Camera Rent Revenue"] += float(c.total_amount)
            monthly_stats[m_key]["Pending Payments"] += float(c.pending_amount)
            
            client_stats[c_key]["Client Name"] = c_key
            client_stats[c_key]["Total Revenue Generated"] += float(c.total_amount)
            client_stats[c_key]["History"].append("Camera Rented")

        # 6. Investments
        for i in investments:
            if not i.date: continue
            m_key = get_month_str(i.date)
            monthly_stats[m_key]["Total Expenses"] += i.total_amount
            monthly_stats[m_key]["Total Investments"] += i.total_amount

        # 7. Pre, On, Post Production Stages
        for p in pre_prods:
            m_key = f"{p.year}-{month_name_to_num(p.month):02d}" if p.year and p.month else "Unknown"
            c_key = p.couple_name
            if m_key != "Unknown":
                monthly_stats[m_key]["Pre-Production Projects"] += 1
                monthly_stats[m_key]["Ongoing Projects"] += 1
            client_stats[c_key]["Client Name"] = c_key
            client_stats[c_key]["Current Project Stage"] = "Pre-Production"

        for o in on_prods:
            m_key = f"{o.year}-{month_name_to_num(o.month):02d}" if o.year and o.month else "Unknown"
            c_key = o.couple_name
            if m_key != "Unknown":
                monthly_stats[m_key]["On-Production Projects"] += 1
                monthly_stats[m_key]["Ongoing Projects"] += 1
            client_stats[c_key]["Client Name"] = c_key
            client_stats[c_key]["Current Project Stage"] = "On-Production"

        for p in post_prods:
            m_key = f"{p.year}-{month_name_to_num(p.month):02d}" if p.year and p.month else "Unknown"
            c_key = p.couple_name
            if m_key != "Unknown":
                monthly_stats[m_key]["Post-Production Projects"] += 1
                if p.closure_date:
                    monthly_stats[m_key]["Completed Projects"] += 1
                else:
                    monthly_stats[m_key]["Ongoing Projects"] += 1
                    
                if p.payment_recovery:
                    monthly_stats[m_key]["Payment Recovery"] += 1
                else:
                    monthly_stats[m_key]["Payment Recovery Pending"] += 1
                    
            client_stats[c_key]["Client Name"] = c_key
            client_stats[c_key]["Current Project Stage"] = "Post-Production" if not p.closure_date else "Completed"


        # Finalize Profit
        for m_key, stats in monthly_stats.items():
            stats["Total Profit"] = stats["Total Revenue"] - stats["Total Expenses"]

        for c_key, c_stats in client_stats.items():
            c_stats["Profit Earned"] = c_stats["Total Revenue Generated"] - c_stats["Total Expenses"] - c_stats["Freelancer Cost"]

        # Sort the monthly_stats by key descending (newest month first)
        sorted_monthly = dict(sorted(monthly_stats.items(), key=lambda item: item[0], reverse=True))
        
        # We may want to filter if user selected specific year/month
        filtered_monthly = {}
        filtered_clients = []
        
        target_m_key = None
        if selected_year != "all":
            if selected_month != "all":
                target_m_key = f"{selected_year}-{int(selected_month):02d}"
            
        for k, v in sorted_monthly.items():
            if target_m_key and k != target_m_key:
                continue
            if selected_year != "all" and not k.startswith(str(selected_year)):
                continue
            filtered_monthly[k] = v
            
        for k, v in client_stats.items():
            if target_m_key and v["Month"] != target_m_key:
                continue
            if selected_year != "all" and v["Month"] and not v["Month"].startswith(str(selected_year)):
                continue
            filtered_clients.append(v)
            
        # Top-level aggregates for Executive Summary Cards based on filtered
        exec_summary = {
            "Total Revenue": sum(v["Total Revenue"] for v in filtered_monthly.values()),
            "Potential Revenue": sum(v["Potential Revenue"] for v in filtered_monthly.values()),
            "Confirmed Revenue": sum(v["Confirmed Revenue"] for v in filtered_monthly.values()),
            "Total Expenses": sum(v["Total Expenses"] for v in filtered_monthly.values()),
            "Freelancer Expenses": sum(v["Freelancer Expenses"] for v in filtered_monthly.values()),
            "Total Investments": sum(v["Total Investments"] for v in filtered_monthly.values()),
            "Total Profit": sum(v["Total Profit"] for v in filtered_monthly.values()),
            "Total Leads": sum(v["Total Leads"] for v in filtered_monthly.values()),
            "Confirmed Clients": sum(v["Confirmed Clients"] for v in filtered_monthly.values()),
            "Rejected Leads": sum(v["Rejected Leads"] for v in filtered_monthly.values()),
            "Upcoming Shoots": sum(v["Upcoming Shoots"] for v in filtered_monthly.values()),
            "Pending Payments": sum(v["Pending Payments"] for v in filtered_monthly.values())
        }

        # Format history string
        for c in filtered_clients:
            c["HistoryStr"] = " | ".join(set(c["History"])) if c["History"] else "No specific logs"

        # Chart datasets
        chart_labels = list(reversed(list(filtered_monthly.keys())))
        chart_revenue = [filtered_monthly[k]["Total Revenue"] for k in chart_labels]
        chart_expenses = [filtered_monthly[k]["Total Expenses"] for k in chart_labels]
        chart_profit = [filtered_monthly[k]["Total Profit"] for k in chart_labels]

        # Top 5 clients by revenue
        top_clients = sorted(filtered_clients, key=lambda x: x["Total Revenue Generated"], reverse=True)[:5]
        top_client_names = [c["Client Name"] for c in top_clients]
        top_client_revs = [c["Total Revenue Generated"] for c in top_clients]

        context = {
            "request": request,
            "page_title": "Monthly Performance Hub",
            "years_list": years_list,
            "months_list": months_list,
            "selected_year": selected_year,
            "selected_month": selected_month,
            
            "exec_summary": exec_summary,
            "monthly_stats": filtered_monthly,
            "client_stats": filtered_clients,
            
            "chart_labels": chart_labels,
            "chart_revenue": chart_revenue,
            "chart_expenses": chart_expenses,
            "chart_profit": chart_profit,
            
            "top_client_names": top_client_names,
            "top_client_revs": top_client_revs
        }

        return templates.TemplateResponse("performance_hub/index.html", context)

    except Exception as e:
        print(f"Error in performance_hub: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": str(e)},
            status_code=500
        )
