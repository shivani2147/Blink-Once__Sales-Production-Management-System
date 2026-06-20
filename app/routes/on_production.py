"""
On-Production module routes for managing on-production day activities.
"""

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import extract
from app.database import get_db
from app.models import OnProduction
from datetime import datetime, date
import calendar
import os

router = APIRouter(prefix="/on-production", tags=["On-Production"])

def normalize_event_date(event_date: str):
    """Normalize event_date to comma-separated day numbers."""
    if not event_date:
        return None
    days = []
    parts = [p.strip() for p in event_date.split(',')]
    for p in parts:
        if '-' in p:
            try:
                d_obj = datetime.strptime(p, "%Y-%m-%d").date()
                days.append(str(d_obj.day))
            except ValueError:
                pass
        elif p.isdigit():
            days.append(str(int(p)))
    return ", ".join(days) if days else None

# Setup templates
template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
templates = Jinja2Templates(directory=template_dir)


@router.get("/", response_class=HTMLResponse)
async def list_on_production(
    request: Request,
    search: str = None,
    year: str = None,
    month: str = None,
    db: Session = Depends(get_db)
):
    """Display list of on-production records."""
    try:
        query = db.query(OnProduction).order_by(OnProduction.created_at.desc())
        
        current_year = datetime.utcnow().year
        years = list(range(2020, current_year + 1))
        months = [(calendar.month_name[i], calendar.month_name[i]) for i in range(1, 13)]
        
        if search:
            query = query.filter(OnProduction.couple_name.ilike(f"%{search}%"))
        if year:
            query = query.filter(OnProduction.year == int(year))
        if month:
            query = query.filter(OnProduction.month == month)
        
        records = query.all()
        
        context = {
            "request": request,
            "page_title": "On-Production",
            "records": records,
            "search_query": search or "",
            "selected_year": year or "",
            "selected_month": month or "",
            "years": years,
            "months": months,
            "current_year": current_year,
            "current_month": calendar.month_name[datetime.utcnow().month]
        }
        
        return templates.TemplateResponse("on_production/list.html", context)
    
    except Exception as e:
        print(f"Error listing on-production records: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": str(e)},
            status_code=500
        )


@router.get("/add", response_class=HTMLResponse)
async def add_on_production_form(request: Request):
    """Display form for adding new on-production record."""
    current_year = datetime.utcnow().year
    years = list(range(2020, current_year + 1))
    months = [(calendar.month_name[i], calendar.month_name[i]) for i in range(1, 13)]
    context = {
        "request": request,
        "page_title": "Add On-Production Record",
        "years": years,
        "months": months,
        "current_year": current_year,
        "current_month": calendar.month_name[datetime.utcnow().month],
        "is_edit": False
    }
    return templates.TemplateResponse("on_production/form.html", context)


@router.post("/add")
async def create_on_production(
    couple_name: str = Form(...),
    event_date: str = Form(...),
    phone_number: str = Form(...),
    client_review: bool = Form(False),
    payment_received: bool = Form(False),
    bts_shoot: bool = Form(False),
    hospitality_gesture: bool = Form(False),
    story_designing_sheet_refer: bool = Form(False),
    checklist_shared_with_team: bool = Form(False),
    assigned_team_members: str = Form(None),
    team_feedback: str = Form(None),
    year: int = Form(None),
    month: str = Form(None),
    notes: str = Form(None),
    db: Session = Depends(get_db)
):
    """Create new on-production record."""
    try:
        # Normalize event_date to day numbers
        event_date_value = normalize_event_date(event_date)
        if not event_date_value:
            raise ValueError("Invalid event_date format. Please select a valid date.")

        record = OnProduction(
            couple_name=couple_name,
            event_date=event_date_value,
            phone_number=phone_number,
            client_review=client_review,
            payment_received=payment_received,
            bts_shoot=bts_shoot,
            hospitality_gesture=hospitality_gesture,
            story_designing_sheet_refer=story_designing_sheet_refer,
            checklist_shared_with_team=checklist_shared_with_team,
            assigned_team_members=assigned_team_members,
            team_feedback=team_feedback,
            year=year,
            month=month,
            notes=notes,
            created_by="Admin"
        )
        
        db.add(record)
        db.commit()
        
        return RedirectResponse(url="/on-production", status_code=303)
    
    except Exception as e:
        db.rollback()
        print(f"Error creating on-production record: {str(e)}")
        raise


@router.get("/{record_id}", response_class=HTMLResponse)
async def view_on_production(
    request: Request,
    record_id: int,
    db: Session = Depends(get_db)
):
    """Display details of a specific on-production record."""
    try:
        record = db.query(OnProduction).filter(OnProduction.id == record_id).first()
        
        if not record:
            return templates.TemplateResponse(
                "error.html",
                {"request": request, "error": "Record not found"},
                status_code=404
            )
        
        context = {
            "request": request,
            "page_title": f"On-Production: {record.couple_name}",
            "record": record,
            "completion_percentage": record.get_completion_percentage(),
        }
        
        return templates.TemplateResponse("on_production/detail.html", context)
    
    except Exception as e:
        print(f"Error viewing on-production record: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": str(e)},
            status_code=500
        )


@router.get("/{record_id}/edit", response_class=HTMLResponse)
async def edit_on_production_form(
    request: Request,
    record_id: int,
    db: Session = Depends(get_db)
):
    """Display form for editing on-production record."""
    try:
        record = db.query(OnProduction).filter(OnProduction.id == record_id).first()
        
        if not record:
            return templates.TemplateResponse(
                "error.html",
                {"request": request, "error": "Record not found"},
                status_code=404
            )
        
        current_year = datetime.utcnow().year
        years = list(range(2020, current_year + 1))
        months = [(calendar.month_name[i], calendar.month_name[i]) for i in range(1, 13)]
        
        context = {
            "request": request,
            "page_title": f"Edit On-Production: {record.couple_name}",
            "record": record,
            "years": years,
            "months": months,
            "is_edit": True
        }
        
        return templates.TemplateResponse("on_production/form.html", context)
    
    except Exception as e:
        print(f"Error loading edit form: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": str(e)},
            status_code=500
        )


@router.post("/{record_id}/edit")
async def update_on_production(
    record_id: int,
    couple_name: str = Form(...),
    event_date: str = Form(...),
    phone_number: str = Form(...),
    client_review: bool = Form(False),
    payment_received: bool = Form(False),
    bts_shoot: bool = Form(False),
    hospitality_gesture: bool = Form(False),
    story_designing_sheet_refer: bool = Form(False),
    checklist_shared_with_team: bool = Form(False),
    assigned_team_members: str = Form(None),
    team_feedback: str = Form(None),
    year: int = Form(None),
    month: str = Form(None),
    notes: str = Form(None),
    db: Session = Depends(get_db)
):
    """Update on-production record."""
    try:
        record = db.query(OnProduction).filter(OnProduction.id == record_id).first()
        
        if not record:
            return {"error": "Record not found"}, 404
        
        # Normalize event_date to day numbers
        event_date_value = normalize_event_date(event_date)
        if not event_date_value:
            raise ValueError("Invalid event_date format. Please select a valid date.")

        record.couple_name = couple_name
        record.event_date = event_date_value
        record.phone_number = phone_number
        record.client_review = client_review
        record.payment_received = payment_received
        record.bts_shoot = bts_shoot
        record.hospitality_gesture = hospitality_gesture
        record.story_designing_sheet_refer = story_designing_sheet_refer
        record.checklist_shared_with_team = checklist_shared_with_team
        record.assigned_team_members = assigned_team_members
        record.team_feedback = team_feedback
        record.year = year
        record.month = month
        record.notes = notes
        record.updated_at = datetime.utcnow()
        
        db.commit()
        
        return RedirectResponse(url="/on-production", status_code=303)
    
    except Exception as e:
        db.rollback()
        print(f"Error updating on-production record: {str(e)}")
        raise


@router.post("/{record_id}/delete")
async def delete_on_production(request: Request,
    record_id: int,
    db: Session = Depends(get_db)
):
    """Delete on-production record."""
    try:
        form = await request.form()
        if form.get("csrf_token") != request.session.get("csrf_token"):
            raise HTTPException(status_code=403, detail="Invalid CSRF token")
        record = db.query(OnProduction).filter(OnProduction.id == record_id).first()
        
        if not record:
            return {"error": "Record not found"}, 404
        
        db.delete(record)
        db.commit()
        
        return RedirectResponse(url="/on-production", status_code=303)
    
    except Exception as e:
        db.rollback()
        print(f"Error deleting on-production record: {str(e)}")
        raise
