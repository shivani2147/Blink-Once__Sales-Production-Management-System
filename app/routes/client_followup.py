"""
Client Follow-up routes - Lead tracking and conversion analytics.
"""

from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import MonthlyFinancialReport, ThreeMonthsClientFollowup
from datetime import datetime, date, timedelta
import secrets
import os
from sqlalchemy import func, extract, case
from .monthly_financial import number_to_words
import json
import re


def create_monthly_report_for_followup(followup: ThreeMonthsClientFollowup, db: Session):
    if followup.status != 'Done':
        return

    # Match by client + year + month + event_type (not event_date, which can change)
    existing = db.query(MonthlyFinancialReport).filter(
        MonthlyFinancialReport.client_name == followup.client_name,
        MonthlyFinancialReport.year == followup.year,
        MonthlyFinancialReport.month == followup.month,
        MonthlyFinancialReport.event_type == followup.event_type,
    ).first()

    if existing:
        # Update existing report to keep it in sync with the followup
        existing.event_date = followup.event_date or ''
        existing.total_amount = followup.total_amount or followup.confirmation or 0.0
        existing.location = followup.location or ''
        existing.requirements = followup.requirements or ''
        existing.calculate_pending()
        existing.calculate_profit()
        db.commit()
        return

    report = MonthlyFinancialReport(
        month=followup.month,
        year=followup.year,
        client_name=followup.client_name,
        project_name='',
        event_type=followup.event_type,
        event_date=followup.event_date or '',
        location=followup.location or '',
        requirements=followup.requirements or '',
        total_amount=followup.total_amount or followup.confirmation or 0.0,
        paid_amount=0.0,
        freelancer_amount=0.0,
        expenses=0.0,
        payment_status='',
        work_status='Pending',
        notes='',
    )
    report.calculate_pending()
    report.calculate_profit()
    db.add(report)
    db.commit()


def delete_monthly_report_for_followup(followup: ThreeMonthsClientFollowup, db: Session):
    """Delete monthly report when followup status is changed away from 'Done'."""
    # Match by client + year + month + event_type (same key as create)
    existing = db.query(MonthlyFinancialReport).filter(
        MonthlyFinancialReport.client_name == followup.client_name,
        MonthlyFinancialReport.year == followup.year,
        MonthlyFinancialReport.month == followup.month,
        MonthlyFinancialReport.event_type == followup.event_type,
    ).first()

    if existing:
        db.delete(existing)
        db.commit()

router = APIRouter(prefix="/financial/followup", tags=["Client Follow-up"])

# Setup templates
template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
templates = Jinja2Templates(directory=template_dir)

# Status options
STATUS_OPTIONS = [
    "Done",
    "Pending",
    "Rejected",
    "Not replied",
    "Quotation sent",
    "Quotation needs to be sent",
    "Meeting in Office",
    "Need to speak",
    "Hold",
    "Advance Payment is pending",
    "Follow up",
]

PLATFORM_OPTIONS = ["JD", "Meta Ads", "Word of Mouth"]


def parse_event_date_days(raw):
    if raw is None:
        return []
    if isinstance(raw, list):
        raw_list = raw
    else:
        raw_text = str(raw).strip()
        if not raw_text:
            return []
        if raw_text.startswith('['):
            try:
                raw_list = json.loads(raw_text)
            except Exception:
                raw_list = re.split(r'[\,;\s]+', raw_text)
        else:
            raw_list = re.split(r'[\,;\s]+', raw_text)

    days = []
    for item in raw_list:
        if item is None:
            continue
        item_text = str(item).strip()
        if not item_text:
            continue
        days.append(item_text)

    return [day for day in days if day]


def normalize_event_date_string(raw):
    days = parse_event_date_days(raw)
    return ', '.join(days)


@router.get("/", response_class=HTMLResponse)
async def list_followups(
    request: Request,
    db: Session = Depends(get_db),
    search: str = None,
    year: str = None,
    month: str = None,
):
    """List all client follow-ups with analytics."""
    try:
        today = date.today()
        three_months_ago = today - timedelta(days=90)
        
        query = db.query(ThreeMonthsClientFollowup).filter(
            ThreeMonthsClientFollowup.date >= three_months_ago
        )
        
        if search:
            query = query.filter(ThreeMonthsClientFollowup.client_name.ilike(f"%{search}%"))
        if year:
            try:
                query = query.filter(ThreeMonthsClientFollowup.year == int(year))
            except ValueError:
                pass
        if month:
            try:
                import calendar
                month_name = month
                if month.isdigit():
                    month_num = int(month)
                    if 1 <= month_num <= 12:
                        month_name = calendar.month_name[month_num]
                query = query.filter(ThreeMonthsClientFollowup.month == month_name)
            except Exception:
                pass
        
        month_order = case(
            (ThreeMonthsClientFollowup.month == 'January', 1),
            (ThreeMonthsClientFollowup.month == 'February', 2),
            (ThreeMonthsClientFollowup.month == 'March', 3),
            (ThreeMonthsClientFollowup.month == 'April', 4),
            (ThreeMonthsClientFollowup.month == 'May', 5),
            (ThreeMonthsClientFollowup.month == 'June', 6),
            (ThreeMonthsClientFollowup.month == 'July', 7),
            (ThreeMonthsClientFollowup.month == 'August', 8),
            (ThreeMonthsClientFollowup.month == 'September', 9),
            (ThreeMonthsClientFollowup.month == 'October', 10),
            (ThreeMonthsClientFollowup.month == 'November', 11),
            (ThreeMonthsClientFollowup.month == 'December', 12),
            else_=0
        )

        followups = query.order_by(ThreeMonthsClientFollowup.year.asc(), month_order.asc(), ThreeMonthsClientFollowup.date.asc()).all()
        
        # Calculate analytics
        total_leads = len(followups)
        done_count = sum(1 for f in followups if f.status == "Done")
        pending_count = sum(1 for f in followups if f.status == "Pending")
        conversion_rate = (done_count / total_leads * 100) if total_leads > 0 else 0
        
        # Calculate totals based on filtered followups
        total_leads_words = number_to_words(total_leads)

        # Financial totals
        total_budget = sum(f.client_budget for f in followups) if followups else 0.0
        total_confirmation = sum(f.confirmation for f in followups) if followups else 0.0
        total_amount = sum(f.total_amount for f in followups) if followups else 0.0
        # Convert totals to words
        total_budget_words = number_to_words(total_budget)
        total_confirmation_words = number_to_words(total_confirmation)
        total_amount_words = number_to_words(total_amount)

        # Platform performance
        platform_stats = {}
        for platform in PLATFORM_OPTIONS:
            count = sum(1 for f in followups if f.platform == platform)
            platform_stats[platform] = count

        # Status-wise breakdown
        status_stats = {}
        for status in STATUS_OPTIONS:
            count = sum(1 for f in followups if f.status == status)
            if count > 0:
                status_stats[status] = count

        # Determine the highest performing platform by number of leads
        if platform_stats:
            top_platform, top_platform_count = max(platform_stats.items(), key=lambda item: item[1])
            top_platform_count_words = number_to_words(top_platform_count)
        else:
            top_platform, top_platform_count = "-", 0
            top_platform_count_words = number_to_words(0)
        
        # Ensure CSRF token exists in session before rendering the list page
        try:
            if request.session.get("csrf_token") is None:
                request.session["csrf_token"] = secrets.token_urlsafe(32)
        except Exception:
            pass

        return templates.TemplateResponse("financial/followup_list.html", {
            "request": request,
            "page_title": "Client Follow-up",
            "top_platform": top_platform,
            "top_platform_count": top_platform_count,
            "followups": followups,
            "total_leads": total_leads,
            "done_count": done_count,
            "pending_count": pending_count,
            "conversion_rate": round(conversion_rate, 2),
            "total_budget": total_budget,
            "total_confirmation": total_confirmation,
            "total_amount": total_amount,
            "total_budget_words": total_budget_words,
            "total_confirmation_words": total_confirmation_words,
            "total_amount_words": total_amount_words,
            "platform_stats": platform_stats,
            "status_stats": status_stats,
            "search_query": search,
            "selected_year": year,
            "selected_month": month,
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        }, status_code=500)



@router.get("/create", response_class=HTMLResponse)
async def create_form(request: Request):
    """Create form is disabled. Redirect to main list."""
    return RedirectResponse(url="/financial/followup/", status_code=302)



@router.post("/create")
async def create_followup(
    request: Request,
    db: Session = Depends(get_db),
    date_input: str = Form(default=""),
    year: int = Form(default=0),
    month: str = Form(default=""),
    client_name: str = Form(default=""),
    event_type: str = Form(default=""),
    event_date: str = Form(default=""),
    location: str = Form(default=""),
    phone_number: str = Form(default=""),
    client_budget: float = Form(default=0.0),
    total_amount: float = Form(default=0.0),
    platform: str = Form(default=""),
    negotiation: bool = Form(default=False),
    confirmation: float = Form(default=0.0),
    status: str = Form(default=""),
    comment: str = Form(default=""),
    requirements: str = Form(default=""),
):
    """Create a new client follow-up from the inline add row."""
    try:
        if not date_input:
            date_input = datetime.now().strftime("%Y-%m-%d")

        days = []
        first_date_obj = datetime.strptime(date_input, "%Y-%m-%d").date()
        if event_date:
            parts = [p.strip() for p in event_date.split(',')]
            for p in parts:
                if '-' in p:
                    try:
                        d_obj = datetime.strptime(p, "%Y-%m-%d").date()
                        days.append(str(d_obj.day))
                        if len(days) == 1:
                            first_date_obj = d_obj
                    except ValueError:
                        pass
                elif p.isdigit():
                    days.append(str(int(p)))
            if parts and all(p.isdigit() for p in parts if p):
                try:
                    day_val = int(parts[0])
                    first_date_obj = date(first_date_obj.year, first_date_obj.month, day_val)
                except ValueError:
                    pass
        event_date_str = ", ".join(days)

        if not month:
            month = first_date_obj.strftime('%B')
        if not year:
            year = first_date_obj.year

        followup = ThreeMonthsClientFollowup(
            date=first_date_obj,
            year=year,
            month=month,
            client_name=client_name,
            event_type=event_type,
            event_date=event_date_str,
            location=location,
            phone_number=phone_number,
            client_budget=client_budget,
            total_amount=total_amount,
            platform=platform,
            negotiation=negotiation,
            confirmation=confirmation,
            status=status,
            comment=comment,
            requirements=requirements,
        )

        db.add(followup)
        db.commit()
        db.refresh(followup)

        create_monthly_report_for_followup(followup, db)
        return RedirectResponse(url="/financial/followup/#add-row-btn", status_code=302)
    except Exception as e:
        print(f"[create_followup] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{followup_id}/edit", response_class=HTMLResponse)
async def edit_form(request: Request, followup_id: int, db: Session = Depends(get_db)):
    """Display form to edit follow-up."""
    try:
        followup = db.query(ThreeMonthsClientFollowup).filter(ThreeMonthsClientFollowup.id == followup_id).first()
        if not followup:
            raise HTTPException(status_code=404, detail="Follow-up not found")
        
        followup.event_date_list = parse_event_date_days(followup.event_date)
        
        display_date = followup.date.strftime('%d/%m/%Y')
        import calendar
        years = list(range(2020, followup.date.year + 1))
        months = [(calendar.month_name[i], calendar.month_name[i]) for i in range(1, 13)]
        # Ensure CSRF token exists in session before rendering
        try:
            if request.session.get("csrf_token") is None:
                request.session["csrf_token"] = secrets.token_urlsafe(32)
        except Exception:
            pass

        return templates.TemplateResponse("financial/followup_form.html", {
            "request": request,
            "page_title": "Edit Client Follow-up",
            "followup": followup,
            "is_edit": True,
            "status_options": STATUS_OPTIONS,
            "platform_options": PLATFORM_OPTIONS,
            "current_date": followup.date.isoformat(),
            "display_date": display_date,
            "years": years,
            "months": months,
            "selected_year": followup.date.year,
            "selected_month": followup.date.strftime('%B'),
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        }, status_code=500)



@router.post("/{followup_id}/edit")
async def edit_followup(
    followup_id: int,
    db: Session = Depends(get_db),
    date_input: str = Form(...),
    year: int = Form(...),
    month: str = Form(...),
    client_name: str = Form(...),
    event_type: str = Form(...),
    event_date: str = Form(default=""),
    location: str = Form(default=""),
    phone_number: str = Form(...),
    client_budget: float = Form(default=0.0),
    total_amount: float = Form(default=0.0),
    platform: str = Form(...),
    negotiation: bool = Form(default=False),
    confirmation: float = Form(0.0),
    status: str = Form(...),
    comment: str = Form(default=""),
    requirements: str = Form(default=""),
):
    """Update client follow-up."""
    try:
        print(f"[edit_followup] Received data - followup_id={followup_id}, year={year}, month={month}, status={status}")
        
        followup = db.query(ThreeMonthsClientFollowup).filter(ThreeMonthsClientFollowup.id == followup_id).first()
        if not followup:
            raise HTTPException(status_code=404, detail="Follow-up not found")
        
        # Store the old status to check if it changed
        old_status = followup.status
        
        # Process event_date and determine day numbers and first event date object
        days = []
        first_date_obj = datetime.strptime(date_input, "%Y-%m-%d").date()
        if event_date:
            parts = [p.strip() for p in event_date.split(',')]
            for p in parts:
                if '-' in p:
                    try:
                        d_obj = datetime.strptime(p, "%Y-%m-%d").date()
                        days.append(str(d_obj.day))
                        if len(days) == 1:
                            first_date_obj = d_obj
                    except ValueError:
                        pass
                elif p.isdigit():
                    days.append(str(int(p)))
            if parts and all(p.isdigit() for p in parts if p):
                try:
                    day_val = int(parts[0])
                    first_date_obj = date(first_date_obj.year, first_date_obj.month, day_val)
                except ValueError:
                    pass
        event_date_str = ", ".join(days)

        followup.date = first_date_obj
        followup.year = year
        followup.month = month
        followup.client_name = client_name
        followup.event_type = event_type
        followup.event_date = event_date_str
        followup.location = location
        followup.phone_number = phone_number
        followup.client_budget = client_budget
        followup.total_amount = total_amount
        followup.platform = platform
        followup.negotiation = negotiation
        followup.confirmation = confirmation
        followup.status = status
        followup.comment = comment
        followup.requirements = requirements
        
        db.commit()
        print(f"[edit_followup] Updated followup, old_status={old_status}, new_status={status}")
        
        # If status changed away from "Done", delete the monthly report
        if old_status == 'Done' and status != 'Done':
            print(f"[edit_followup] Status changed from Done to {status}, deleting monthly report")
            delete_monthly_report_for_followup(followup, db)
        else:
            # If status is "Done", create or keep the monthly report
            print(f"[edit_followup] Status is {status}, creating/maintaining monthly report")
            create_monthly_report_for_followup(followup, db)
        
        return RedirectResponse(url="/financial/followup/", status_code=302)
    except Exception as e:
        print(f"[edit_followup] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{followup_id}/delete")
async def delete_followup(request: Request, followup_id: int, db: Session = Depends(get_db)):
    """Delete client follow-up."""
    try:
        # Read form and convert to plain dict for easier inspection
        form = await request.form()
        form_dict = {k: v for k, v in form.items()}
        form_token = form_dict.get("csrf_token")
        session_token = None
        try:
            session_token = request.session.get("csrf_token")
        except Exception:
            session_token = None

        # Debug prints to server console to help diagnose requests
        print(f"[delete_followup] method={request.method} followup_id={followup_id} form_keys={list(form_dict.keys())} form_token={form_token!r} session_token={session_token!r}")

        if form_token != session_token:
            # Provide clearer error for client and server logs
            detail = f"Invalid CSRF token (form={form_token!r}, session={session_token!r})"
            print("[delete_followup] CSRF mismatch:", detail)
            raise HTTPException(status_code=403, detail=detail)
        followup = db.query(ThreeMonthsClientFollowup).filter(ThreeMonthsClientFollowup.id == followup_id).first()
        if not followup:
            raise HTTPException(status_code=404, detail="Follow-up not found")
        
        # Delete associated monthly report if it exists
        delete_monthly_report_for_followup(followup, db)
        
        db.delete(followup)
        db.commit()
        
        return RedirectResponse(url="/financial/followup/", status_code=302)
    except HTTPException:
        # Re-raise known HTTP errors unchanged so FastAPI handles status codes
        raise
    except Exception as e:
        # Log unexpected errors and return a clearer message
        print(f"[delete_followup] unexpected error: {e}")
        raise HTTPException(status_code=400, detail=f"Error deleting follow-up: {e}")


@router.get("/{followup_id}/detail", response_class=HTMLResponse)
async def detail_followup(request: Request, followup_id: int, db: Session = Depends(get_db)):
    """Display detailed view of a follow-up."""
    try:
        followup = db.query(ThreeMonthsClientFollowup).filter(ThreeMonthsClientFollowup.id == followup_id).first()
        if not followup:
            raise HTTPException(status_code=404, detail="Follow-up not found")
        
        followup.event_date_list = parse_event_date_days(followup.event_date)
        
        # Ensure CSRF token exists in session before rendering
        try:
            if request.session.get("csrf_token") is None:
                request.session["csrf_token"] = secrets.token_urlsafe(32)
        except Exception:
            pass

        return templates.TemplateResponse("financial/followup_detail.html", {
            "request": request,
            "page_title": "Client Follow-up Details",
            "followup": followup,
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        }, status_code=500)
