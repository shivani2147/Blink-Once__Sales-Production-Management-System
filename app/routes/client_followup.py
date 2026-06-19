"""
Client Follow-up routes - Lead tracking and conversion analytics.
"""

from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import ThreeMonthsClientFollowup
from datetime import datetime, date, timedelta
import os
from sqlalchemy import func, extract
from .monthly_financial import number_to_words
import re

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
                query = query.filter(extract('year', ThreeMonthsClientFollowup.date) == int(year))
            except ValueError:
                pass
        if month:
            try:
                query = query.filter(extract('month', ThreeMonthsClientFollowup.date) == int(month))
            except ValueError:
                pass
        
        followups = query.order_by(ThreeMonthsClientFollowup.date.desc()).all()
        
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
    """Display form to create new follow-up with auto-filled current date."""
    try:
        today = datetime.now().date()
        display_date = today.strftime('%d/%m/%Y')
        return templates.TemplateResponse("financial/followup_form.html", {
            "request": request,
            "page_title": "Client Follow-up",
            "is_edit": False,
            "status_options": STATUS_OPTIONS,
            "platform_options": PLATFORM_OPTIONS,
            "current_date": today.isoformat(),
            "display_date": display_date,
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        }, status_code=500)


@router.post("/create")
async def create_followup(
    request: Request,
    db: Session = Depends(get_db),
    date_input: str = Form(...),
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
):
    """Create new client follow-up."""
    try:
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

        followup = ThreeMonthsClientFollowup(
            date=first_date_obj,
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
        )
        
        db.add(followup)
        db.commit()
        
        return RedirectResponse(url="/financial/followup/", status_code=302)
    except Exception as e:
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
        
        return templates.TemplateResponse("financial/followup_form.html", {
            "request": request,
            "page_title": "Edit Client Follow-up",
            "followup": followup,
            "is_edit": True,
            "status_options": STATUS_OPTIONS,
            "platform_options": PLATFORM_OPTIONS,
            "current_date": followup.date.isoformat(),
            "display_date": display_date,
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
):
    """Update client follow-up."""
    try:
        followup = db.query(ThreeMonthsClientFollowup).filter(ThreeMonthsClientFollowup.id == followup_id).first()
        if not followup:
            raise HTTPException(status_code=404, detail="Follow-up not found")
        
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
        
        db.commit()
        return RedirectResponse(url="/financial/followup/", status_code=302)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{followup_id}/delete")
async def delete_followup(followup_id: int, db: Session = Depends(get_db)):
    """Delete client follow-up."""
    try:
        followup = db.query(ThreeMonthsClientFollowup).filter(ThreeMonthsClientFollowup.id == followup_id).first()
        if not followup:
            raise HTTPException(status_code=404, detail="Follow-up not found")
        
        db.delete(followup)
        db.commit()
        
        return RedirectResponse(url="/financial/followup/", status_code=302)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{followup_id}/detail", response_class=HTMLResponse)
async def detail_followup(request: Request, followup_id: int, db: Session = Depends(get_db)):
    """Display detailed view of a follow-up."""
    try:
        followup = db.query(ThreeMonthsClientFollowup).filter(ThreeMonthsClientFollowup.id == followup_id).first()
        if not followup:
            raise HTTPException(status_code=404, detail="Follow-up not found")
        
        followup.event_date_list = parse_event_date_days(followup.event_date)
        
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
