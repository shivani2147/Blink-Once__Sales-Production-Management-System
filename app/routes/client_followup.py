"""
3 Months Client Follow-up routes - Lead tracking and conversion analytics.
"""

from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import ThreeMonthsClientFollowup
from datetime import datetime, date, timedelta
import os
from sqlalchemy import func
import json

router = APIRouter(prefix="/financial/followup", tags=["3 Months Client Follow-up"])

# Setup templates
template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
templates = Jinja2Templates(directory=template_dir)

# Status options
STATUS_OPTIONS = ["Done", "Pending", "Rejected", "Not replied", "Quotation sent", 
                  "Quotation needs to be sent", "Meeting in Office", "Need to speak", "Hold"]

PLATFORM_OPTIONS = ["JD", "Meta Ads", "Word of Mouth"]


@router.get("/", response_class=HTMLResponse)
async def list_followups(request: Request, db: Session = Depends(get_db)):
    """List all 3 months client follow-ups with analytics."""
    try:
        today = date.today()
        three_months_ago = today - timedelta(days=90)
        
        followups = db.query(ThreeMonthsClientFollowup).filter(
            ThreeMonthsClientFollowup.date >= three_months_ago
        ).order_by(ThreeMonthsClientFollowup.date.desc()).all()
        
        # Calculate analytics
        total_leads = len(followups)
        done_count = sum(1 for f in followups if f.status == "Done")
        pending_count = sum(1 for f in followups if f.status == "Pending")
        conversion_rate = (done_count / total_leads * 100) if total_leads > 0 else 0
        
        total_budget = db.query(func.sum(ThreeMonthsClientFollowup.client_budget)).filter(
            ThreeMonthsClientFollowup.date >= three_months_ago
        ).scalar() or 0.0
        total_confirmation = db.query(func.sum(ThreeMonthsClientFollowup.confirmation)).filter(
            ThreeMonthsClientFollowup.date >= three_months_ago
        ).scalar() or 0.0
        total_amount = db.query(func.sum(ThreeMonthsClientFollowup.total_amount)).filter(
            ThreeMonthsClientFollowup.date >= three_months_ago
        ).scalar() or 0.0
        
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
        else:
            top_platform, top_platform_count = "N/A", 0
        
        return templates.TemplateResponse("financial/followup_list.html", {
            "request": request,
            "page_title": "3 Months Client Follow-up",
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
            "platform_stats": platform_stats,
            "status_stats": status_stats,
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        }, status_code=500)


@router.get("/create", response_class=HTMLResponse)
async def create_form(request: Request):
    """Display form to create new follow-up."""
    try:
        return templates.TemplateResponse("financial/followup_form.html", {
            "request": request,
            "page_title": "Create Client Follow-up",
            "is_edit": False,
            "status_options": STATUS_OPTIONS,
            "platform_options": PLATFORM_OPTIONS,
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
    event_date: str = Form(...),
    location: str = Form(default=""),
    phone_number: str = Form(...),
    client_budget: float = Form(...),
    total_amount: float = Form(...),
    platform: str = Form(...),
    negotiation: bool = Form(default=False),
    confirmation: float = Form(0.0),
    status: str = Form(...),
    comment: str = Form(default=""),
):
    """Create new client follow-up."""
    try:
        # Parse event_date (JSON array or single date)
        event_date_list = []
        try:
            event_date_list = json.loads(event_date)
            if not isinstance(event_date_list, list):
                event_date_list = [event_date]
        except:
            event_date_list = [event_date]
        
        # Use first date for the database field
        first_event_date = event_date_list[0] if event_date_list else event_date
        
        # Store all dates as JSON string
        event_date_json = json.dumps(event_date_list)
        
        followup = ThreeMonthsClientFollowup(
            date=datetime.strptime(date_input, "%Y-%m-%d").date(),
            client_name=client_name,
            event_type=event_type,
            event_date=event_date_json,
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
        
        # Parse event_date to get list of dates
        event_date_list = []
        try:
            # Try to parse as JSON (multiple dates)
            event_date_list = json.loads(str(followup.event_date))
            if not isinstance(event_date_list, list):
                event_date_list = [followup.event_date.strftime('%Y-%m-%d')]
        except:
            # Fallback to single date
            event_date_list = [followup.event_date.strftime('%Y-%m-%d')]
        
        followup.event_date_list = event_date_list
        
        return templates.TemplateResponse("financial/followup_form.html", {
            "request": request,
            "page_title": "Edit Client Follow-up",
            "followup": followup,
            "is_edit": True,
            "status_options": STATUS_OPTIONS,
            "platform_options": PLATFORM_OPTIONS,
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
    event_date: str = Form(...),
    location: str = Form(default=""),
    phone_number: str = Form(...),
    client_budget: float = Form(...),
    total_amount: float = Form(...),
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
        
        # Parse event_date (JSON array or single date)
        event_date_list = []
        try:
            event_date_list = json.loads(event_date)
            if not isinstance(event_date_list, list):
                event_date_list = [event_date]
        except:
            event_date_list = [event_date]
        
        # Store all dates as JSON string
        event_date_json = json.dumps(event_date_list)
        
        followup.date = datetime.strptime(date_input, "%Y-%m-%d").date()
        followup.client_name = client_name
        followup.event_type = event_type
        followup.event_date = event_date_json
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
        
        # Parse event_date to get list of dates
        event_date_list = []
        try:
            # Try to parse as JSON (multiple dates)
            event_date_list = json.loads(str(followup.event_date))
            if not isinstance(event_date_list, list):
                event_date_list = [followup.event_date.strftime('%d %b %Y') if isinstance(followup.event_date, date) else followup.event_date]
            else:
                # Convert dates to formatted strings
                event_date_list = [datetime.strptime(d, '%Y-%m-%d').strftime('%d %b %Y') if isinstance(d, str) else d for d in event_date_list]
        except:
            # Fallback to single date
            if isinstance(followup.event_date, date):
                event_date_list = [followup.event_date.strftime('%d %b %Y')]
            else:
                event_date_list = [str(followup.event_date)]
        
        followup.event_date_list = event_date_list
        
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
