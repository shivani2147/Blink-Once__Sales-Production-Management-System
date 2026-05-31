"""
Pre-Production module routes for managing pre-production activities.
"""

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import PreProduction
from datetime import datetime
import os

router = APIRouter(prefix="/pre-production", tags=["Pre-Production"])

# Setup templates
template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
templates = Jinja2Templates(directory=template_dir)


@router.get("/", response_class=HTMLResponse)
async def list_pre_production(
    request: Request,
    search: str = None,
    year: str = None,
    month: str = None,
    db: Session = Depends(get_db)
):
    """Display list of pre-production records with search functionality."""
    try:
        query = db.query(PreProduction).order_by(PreProduction.created_at.desc())
        
        if search:
            query = query.filter(PreProduction.couple_name.ilike(f"%{search}%"))
        if year or month:
            if month:
                month = month.zfill(2)
            pattern = f"{year or '%'}-{month or '%'}-%"
            query = query.filter(PreProduction.event_date.ilike(pattern))
        
        records = query.all()
        
        context = {
            "request": request,
            "page_title": "Pre-Production",
            "records": records,
            "search_query": search or "",
            "selected_year": year or "",
            "selected_month": month or "",
        }
        
        return templates.TemplateResponse("pre_production/list.html", context)
    
    except Exception as e:
        print(f"Error listing pre-production records: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": str(e)},
            status_code=500
        )


@router.get("/add", response_class=HTMLResponse)
async def add_pre_production_form(request: Request):
    """Display form for adding new pre-production record."""
    context = {
        "request": request,
        "page_title": "Add Pre-Production Record",
    }
    return templates.TemplateResponse("pre_production/form.html", context)


@router.post("/add")
async def create_pre_production(
    couple_name: str = Form(...),
    client_email: str = Form(...),
    event_type: str = Form(...),
    event_date: str = Form(...),
    phone_number: str = Form(...),
    referral_program: bool = Form(False),
    advance_retainer_received: bool = Form(False),
    welcome_call: bool = Form(False),
    team_booking: bool = Form(False),
    story_designing_call: bool = Form(False),
    heartfelt_email_cra: bool = Form(False),
    terms_confirmation_cra: bool = Form(False),
    invoicing_cra: bool = Form(False),
    sending_jd_to_team: bool = Form(False),
    music_choice_link_cra: bool = Form(False),
    invitation_video: bool = Form(False),
    whatsapp_group: bool = Form(False),
    notes: str = Form(None),
    db: Session = Depends(get_db)
):
    """Create new pre-production record."""
    try:
        record = PreProduction(
            couple_name=couple_name,
            client_email=client_email,
            event_type=event_type,
            event_date=event_date,
            phone_number=phone_number,
            referral_program=referral_program,
            advance_retainer_received=advance_retainer_received,
            welcome_call=welcome_call,
            team_booking=team_booking,
            story_designing_call=story_designing_call,
            heartfelt_email_cra=heartfelt_email_cra,
            terms_confirmation_cra=terms_confirmation_cra,
            invoicing_cra=invoicing_cra,
            sending_jd_to_team=sending_jd_to_team,
            music_choice_link_cra=music_choice_link_cra,
            invitation_video=invitation_video,
            whatsapp_group=whatsapp_group,
            notes=notes,
            created_by="Admin"
        )
        
        db.add(record)
        db.commit()
        db.refresh(record)
        
        return RedirectResponse(url="/pre-production", status_code=303)
    
    except Exception as e:
        db.rollback()
        print(f"Error creating pre-production record: {str(e)}")
        raise


@router.get("/{record_id}", response_class=HTMLResponse)
async def view_pre_production(
    request: Request,
    record_id: int,
    db: Session = Depends(get_db)
):
    """Display details of a specific pre-production record."""
    try:
        record = db.query(PreProduction).filter(PreProduction.id == record_id).first()
        
        if not record:
            return templates.TemplateResponse(
                "error.html",
                {"request": request, "error": "Record not found"},
                status_code=404
            )
        
        context = {
            "request": request,
            "page_title": f"Pre-Production: {record.couple_name}",
            "record": record,
            "completion_percentage": record.get_completion_percentage(),
        }
        
        return templates.TemplateResponse("pre_production/detail.html", context)
    
    except Exception as e:
        print(f"Error viewing pre-production record: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": str(e)},
            status_code=500
        )


@router.get("/{record_id}/edit", response_class=HTMLResponse)
async def edit_pre_production_form(
    request: Request,
    record_id: int,
    db: Session = Depends(get_db)
):
    """Display form for editing pre-production record."""
    try:
        record = db.query(PreProduction).filter(PreProduction.id == record_id).first()
        
        if not record:
            return templates.TemplateResponse(
                "error.html",
                {"request": request, "error": "Record not found"},
                status_code=404
            )
        
        context = {
            "request": request,
            "page_title": f"Edit Pre-Production: {record.couple_name}",
            "record": record,
        }
        
        return templates.TemplateResponse("pre_production/form.html", context)
    
    except Exception as e:
        print(f"Error loading edit form: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": str(e)},
            status_code=500
        )


@router.post("/{record_id}/edit")
async def update_pre_production(
    record_id: int,
    couple_name: str = Form(...),
    client_email: str = Form(...),
    event_type: str = Form(...),
    event_date: str = Form(...),
    phone_number: str = Form(...),
    referral_program: bool = Form(False),
    advance_retainer_received: bool = Form(False),
    welcome_call: bool = Form(False),
    team_booking: bool = Form(False),
    story_designing_call: bool = Form(False),
    heartfelt_email_cra: bool = Form(False),
    terms_confirmation_cra: bool = Form(False),
    invoicing_cra: bool = Form(False),
    sending_jd_to_team: bool = Form(False),
    music_choice_link_cra: bool = Form(False),
    invitation_video: bool = Form(False),
    whatsapp_group: bool = Form(False),
    notes: str = Form(None),
    db: Session = Depends(get_db)
):
    """Update pre-production record."""
    try:
        record = db.query(PreProduction).filter(PreProduction.id == record_id).first()
        
        if not record:
            return {"error": "Record not found"}, 404
        
        record.couple_name = couple_name
        record.client_email = client_email
        record.event_type = event_type
        record.event_date = event_date
        record.phone_number = phone_number
        record.referral_program = referral_program
        record.advance_retainer_received = advance_retainer_received
        record.welcome_call = welcome_call
        record.team_booking = team_booking
        record.story_designing_call = story_designing_call
        record.heartfelt_email_cra = heartfelt_email_cra
        record.terms_confirmation_cra = terms_confirmation_cra
        record.invoicing_cra = invoicing_cra
        record.sending_jd_to_team = sending_jd_to_team
        record.music_choice_link_cra = music_choice_link_cra
        record.invitation_video = invitation_video
        record.whatsapp_group = whatsapp_group
        record.notes = notes
        record.updated_at = datetime.utcnow()
        
        db.commit()
        
        return RedirectResponse(url=f"/pre-production/{record_id}", status_code=303)
    
    except Exception as e:
        db.rollback()
        print(f"Error updating pre-production record: {str(e)}")
        raise


@router.post("/{record_id}/delete")
async def delete_pre_production(
    record_id: int,
    db: Session = Depends(get_db)
):
    """Delete pre-production record."""
    try:
        record = db.query(PreProduction).filter(PreProduction.id == record_id).first()
        
        if not record:
            return {"error": "Record not found"}, 404
        
        db.delete(record)
        db.commit()
        
        return RedirectResponse(url="/pre-production", status_code=303)
    
    except Exception as e:
        db.rollback()
        print(f"Error deleting pre-production record: {str(e)}")
        raise
