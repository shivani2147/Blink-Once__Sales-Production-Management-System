"""
Post-Production module routes for managing post-production deliverables.
"""

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import extract
from app.database import get_db
from app.models import PostProduction
from datetime import datetime, date
import calendar
import os

router = APIRouter(prefix="/post-production", tags=["Post-Production"])

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
async def list_post_production(
    request: Request,
    search: str = None,
    year: str = None,
    month: str = None,
    db: Session = Depends(get_db)
):
    """Display list of post-production records."""
    try:
        query = db.query(PostProduction).order_by(PostProduction.created_at.desc())
        
        current_year = datetime.utcnow().year
        years = list(range(2020, current_year + 1))
        months = [(calendar.month_name[i], calendar.month_name[i]) for i in range(1, 13)]
        
        if search:
            query = query.filter(PostProduction.couple_name.ilike(f"%{search}%"))
        if year:
            query = query.filter(PostProduction.year == int(year))
        if month:
            query = query.filter(PostProduction.month == month)
        
        records = query.all()
        
        context = {
            "request": request,
            "page_title": "Post-Production",
            "records": records,
            "search_query": search or "",
            "selected_year": year or "",
            "selected_month": month or "",
            "years": years,
            "months": months,
            "current_year": current_year,
            "current_month": calendar.month_name[datetime.utcnow().month]
        }
        
        return templates.TemplateResponse("post_production/list.html", context)
    
    except Exception as e:
        print(f"Error listing post-production records: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": str(e)},
            status_code=500
        )


@router.get("/add", response_class=HTMLResponse)
async def add_post_production_form(request: Request):
    """Display form for adding new post-production record."""
    current_year = datetime.utcnow().year
    years = list(range(2020, current_year + 1))
    months = [(calendar.month_name[i], calendar.month_name[i]) for i in range(1, 13)]
    context = {
        "request": request,
        "page_title": "Add Post-Production Record",
        "years": years,
        "months": months,
        "current_year": current_year,
        "current_month": calendar.month_name[datetime.utcnow().month],
        "is_edit": False
    }
    return templates.TemplateResponse("post_production/form.html", context)


@router.post("/add")
async def create_post_production(
    couple_name: str = Form(...),
    event_date: str = Form(...),
    deadline: str = Form(...),
    event_name: str = Form(None),
    closure_date: str = Form(None),
    data_copy: bool = Form(False),
    best_couple_edits_3_days: bool = Form(False),
    all_raw_images: bool = Form(False),
    save_the_date: bool = Form(False),
    invite: bool = Form(False),
    countdown: bool = Form(False),
    celebrity_ai_reel: bool = Form(False),
    one_teaser: bool = Form(False),
    one_film: bool = Form(False),
    one_reel: bool = Form(False),
    full_length_film: bool = Form(False),
    edited_images_selection: bool = Form(False),
    edited_images_delivered: bool = Form(False),
    poster: bool = Form(False),
    albums_picture_selection: bool = Form(False),
    photobook_delivered: bool = Form(False),
    digital_portfolio_album: bool = Form(False),
    payment_recovery: bool = Form(False),
    year: int = Form(None),
    month: str = Form(None),
    remarks: str = Form(None),
    db: Session = Depends(get_db)
):
    """Create new post-production record."""
    try:
        # Normalize event_date to day numbers
        event_date_value = normalize_event_date(event_date)
        if not event_date_value:
            raise ValueError("Invalid event_date format. Please select a valid date.")

        record = PostProduction(
            couple_name=couple_name,
            event_date=event_date_value,
            deadline=datetime.strptime(deadline, "%Y-%m-%d").date(),
            event_name=event_name,
            data_copy=data_copy,
            best_couple_edits_3_days=best_couple_edits_3_days,
            all_raw_images=all_raw_images,
            save_the_date=save_the_date,
            invite=invite,
            countdown=countdown,
            celebrity_ai_reel=celebrity_ai_reel,
            one_teaser=one_teaser,
            one_film=one_film,
            one_reel=one_reel,
            full_length_film=full_length_film,
            edited_images_selection=edited_images_selection,
            edited_images_delivered=edited_images_delivered,
            poster=poster,
            albums_picture_selection=albums_picture_selection,
            photobook_delivered=photobook_delivered,
            digital_portfolio_album=digital_portfolio_album,
            payment_recovery=payment_recovery,
            closure_date=datetime.strptime(closure_date, "%Y-%m-%d").date() if closure_date else None,
            year=year,
            month=month,
            remarks=remarks,
            created_by="Admin"
        )
        
        db.add(record)
        db.commit()
        
        return RedirectResponse(url="/post-production", status_code=303)
    
    except Exception as e:
        db.rollback()
        print(f"Error creating post-production record: {str(e)}")
        raise


@router.get("/{record_id}", response_class=HTMLResponse)
async def view_post_production(
    request: Request,
    record_id: int,
    db: Session = Depends(get_db)
):
    """Display details of a specific post-production record."""
    try:
        record = db.query(PostProduction).filter(PostProduction.id == record_id).first()
        
        if not record:
            return templates.TemplateResponse(
                "error.html",
                {"request": request, "error": "Record not found"},
                status_code=404
            )
        
        context = {
            "request": request,
            "page_title": f"Post-Production: {record.couple_name}",
            "record": record,
            "completion_percentage": record.get_completion_percentage(),
            "is_overdue": record.is_overdue(),
        }
        
        return templates.TemplateResponse("post_production/detail.html", context)
    
    except Exception as e:
        print(f"Error viewing post-production record: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": str(e)},
            status_code=500
        )


@router.get("/{record_id}/edit", response_class=HTMLResponse)
async def edit_post_production_form(
    request: Request,
    record_id: int,
    db: Session = Depends(get_db)
):
    """Display form for editing post-production record."""
    try:
        record = db.query(PostProduction).filter(PostProduction.id == record_id).first()
        
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
            "page_title": f"Edit Post-Production: {record.couple_name}",
            "record": record,
            "years": years,
            "months": months,
            "is_edit": True
        }
        
        return templates.TemplateResponse("post_production/form.html", context)
    
    except Exception as e:
        print(f"Error loading edit form: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": str(e)},
            status_code=500
        )


@router.post("/{record_id}/edit")
async def update_post_production(
    record_id: int,
    couple_name: str = Form(...),
    event_date: str = Form(...),
    deadline: str = Form(...),
    event_name: str = Form(None),
    closure_date: str = Form(None),
    data_copy: bool = Form(False),
    best_couple_edits_3_days: bool = Form(False),
    all_raw_images: bool = Form(False),
    save_the_date: bool = Form(False),
    invite: bool = Form(False),
    countdown: bool = Form(False),
    celebrity_ai_reel: bool = Form(False),
    one_teaser: bool = Form(False),
    one_film: bool = Form(False),
    one_reel: bool = Form(False),
    full_length_film: bool = Form(False),
    edited_images_selection: bool = Form(False),
    edited_images_delivered: bool = Form(False),
    poster: bool = Form(False),
    albums_picture_selection: bool = Form(False),
    photobook_delivered: bool = Form(False),
    digital_portfolio_album: bool = Form(False),
    payment_recovery: bool = Form(False),
    year: int = Form(None),
    month: str = Form(None),
    remarks: str = Form(None),
    db: Session = Depends(get_db)
):
    """Update post-production record."""
    try:
        record = db.query(PostProduction).filter(PostProduction.id == record_id).first()
        
        if not record:
            return {"error": "Record not found"}, 404
        
        # Normalize event_date to day numbers
        event_date_value = normalize_event_date(event_date)
        if not event_date_value:
            raise ValueError("Invalid event_date format. Please select a valid date.")

        record.couple_name = couple_name
        record.event_date = event_date_value
        record.deadline = datetime.strptime(deadline, "%Y-%m-%d").date()
        record.closure_date = datetime.strptime(closure_date, "%Y-%m-%d").date() if closure_date else None
        record.event_name = event_name
        record.data_copy = data_copy
        record.best_couple_edits_3_days = best_couple_edits_3_days
        record.all_raw_images = all_raw_images
        record.save_the_date = save_the_date
        record.invite = invite
        record.countdown = countdown
        record.celebrity_ai_reel = celebrity_ai_reel
        record.one_teaser = one_teaser
        record.one_film = one_film
        record.one_reel = one_reel
        record.full_length_film = full_length_film
        record.edited_images_selection = edited_images_selection
        record.edited_images_delivered = edited_images_delivered
        record.poster = poster
        record.albums_picture_selection = albums_picture_selection
        record.photobook_delivered = photobook_delivered
        record.digital_portfolio_album = digital_portfolio_album
        record.payment_recovery = payment_recovery
        record.year = year
        record.month = month
        record.remarks = remarks
        record.updated_at = datetime.utcnow()
        
        db.commit()
        
        return RedirectResponse(url="/post-production", status_code=303)
    
    except Exception as e:
        db.rollback()
        print(f"Error updating post-production record: {str(e)}")
        raise


@router.post("/{record_id}/delete")
async def delete_post_production(
    record_id: int,
    db: Session = Depends(get_db)
):
    """Delete post-production record."""
    try:
        record = db.query(PostProduction).filter(PostProduction.id == record_id).first()
        
        if not record:
            return {"error": "Record not found"}, 404
        
        db.delete(record)
        db.commit()
        
        return RedirectResponse(url="/post-production", status_code=303)
    
    except Exception as e:
        db.rollback()
        print(f"Error deleting post-production record: {str(e)}")
        raise
