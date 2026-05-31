"""
Upcoming Clients Shoot routes - Shoot scheduling and pipeline management.
"""

from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import UpcomingClientsShoot
from datetime import datetime, date, timedelta
import os
from sqlalchemy import func

router = APIRouter(prefix="/financial/upcoming-shoots", tags=["Upcoming Clients Shoot"])

# Setup templates
template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
templates = Jinja2Templates(directory=template_dir)


@router.get("/", response_class=HTMLResponse)
async def list_upcoming_shoots(request: Request, db: Session = Depends(get_db)):
    """List all upcoming shoots with analytics."""
    try:
        today = date.today()
        upcoming_shoots = db.query(UpcomingClientsShoot).filter(
            UpcomingClientsShoot.event_date >= today
        ).order_by(UpcomingClientsShoot.event_date).all()
        
        # Calculate analytics
        total_shoots = len(upcoming_shoots)
        total_potential_revenue = db.query(func.sum(UpcomingClientsShoot.total_amount)).filter(
            UpcomingClientsShoot.event_date >= today
        ).scalar() or 0.0
        
        # Status breakdown
        pending_count = sum(1 for s in upcoming_shoots if s.status == "Pending")
        done_count = sum(1 for s in upcoming_shoots if s.status == "Done")
        rejected_count = sum(1 for s in upcoming_shoots if s.status == "Rejected")
        
        # Confirmation status
        confirmed_shoots = sum(1 for s in upcoming_shoots if s.confirmation)
        
        # This week's shoots
        week_end = today + timedelta(days=7)
        this_week_shoots = sum(1 for s in upcoming_shoots if s.event_date <= week_end)
        
        return templates.TemplateResponse("financial/upcoming_shoots_list.html", {
            "request": request,
            "page_title": "Upcoming Clients Shoot",
            "shoots": upcoming_shoots,
            "total_shoots": total_shoots,
            "total_potential_revenue": total_potential_revenue,
            "pending_count": pending_count,
            "done_count": done_count,
            "rejected_count": rejected_count,
            "confirmed_shoots": confirmed_shoots,
            "this_week_shoots": this_week_shoots,
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        }, status_code=500)


@router.get("/create", response_class=HTMLResponse)
async def create_form(request: Request):
    """Display form to create new upcoming shoot."""
    try:
        return templates.TemplateResponse("financial/upcoming_shoots_form.html", {
            "request": request,
            "page_title": "Create Upcoming Shoot",
            "is_edit": False,
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        }, status_code=500)


@router.post("/create")
async def create_shoot(
    request: Request,
    db: Session = Depends(get_db),
    date_input: str = Form(...),
    client_name: str = Form(...),
    event_type: str = Form(...),
    event_date: str = Form(...),
    phone_number: str = Form(...),
    total_amount: float = Form(...),
    negotiation: bool = Form(default=False),
    confirmation: bool = Form(default=False),
    status: str = Form(...),
    notes: str = Form(default=""),
):
    """Create new upcoming shoot."""
    try:
        shoot = UpcomingClientsShoot(
            date=datetime.strptime(date_input, "%Y-%m-%d").date(),
            client_name=client_name,
            event_type=event_type,
            event_date=event_date,
            phone_number=phone_number,
            total_amount=total_amount,
            negotiation=negotiation,
            confirmation=confirmation,
            status=status,
            notes=notes,
        )
        
        db.add(shoot)
        db.commit()
        
        return RedirectResponse(url="/financial/upcoming-shoots/", status_code=302)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{shoot_id}/edit", response_class=HTMLResponse)
async def edit_form(request: Request, shoot_id: int, db: Session = Depends(get_db)):
    """Display form to edit upcoming shoot."""
    try:
        shoot = db.query(UpcomingClientsShoot).filter(UpcomingClientsShoot.id == shoot_id).first()
        if not shoot:
            raise HTTPException(status_code=404, detail="Shoot not found")
        
        return templates.TemplateResponse("financial/upcoming_shoots_form.html", {
            "request": request,
            "page_title": "Edit Upcoming Shoot",
            "shoot": shoot,
            "is_edit": True,
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        }, status_code=500)


@router.post("/{shoot_id}/edit")
async def edit_shoot(
    shoot_id: int,
    db: Session = Depends(get_db),
    date_input: str = Form(...),
    client_name: str = Form(...),
    event_type: str = Form(...),
    event_date: str = Form(...),
    phone_number: str = Form(...),
    total_amount: float = Form(...),
    negotiation: bool = Form(default=False),
    confirmation: bool = Form(default=False),
    status: str = Form(...),
    notes: str = Form(default=""),
):
    """Update upcoming shoot."""
    try:
        shoot = db.query(UpcomingClientsShoot).filter(UpcomingClientsShoot.id == shoot_id).first()
        if not shoot:
            raise HTTPException(status_code=404, detail="Shoot not found")
        
        shoot.date = datetime.strptime(date_input, "%Y-%m-%d").date()
        shoot.client_name = client_name
        shoot.event_type = event_type
        shoot.event_date = event_date
        shoot.phone_number = phone_number
        shoot.total_amount = total_amount
        shoot.negotiation = negotiation
        shoot.confirmation = confirmation
        shoot.status = status
        shoot.notes = notes
        
        db.commit()
        return RedirectResponse(url="/financial/upcoming-shoots/", status_code=302)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{shoot_id}/delete")
async def delete_shoot(shoot_id: int, db: Session = Depends(get_db)):
    """Delete upcoming shoot."""
    try:
        shoot = db.query(UpcomingClientsShoot).filter(UpcomingClientsShoot.id == shoot_id).first()
        if not shoot:
            raise HTTPException(status_code=404, detail="Shoot not found")
        
        db.delete(shoot)
        db.commit()
        
        return RedirectResponse(url="/financial/upcoming-shoots/", status_code=302)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{shoot_id}/detail", response_class=HTMLResponse)
async def detail_shoot(request: Request, shoot_id: int, db: Session = Depends(get_db)):
    """Display detailed view of an upcoming shoot."""
    try:
        shoot = db.query(UpcomingClientsShoot).filter(UpcomingClientsShoot.id == shoot_id).first()
        if not shoot:
            raise HTTPException(status_code=404, detail="Shoot not found")
        
        return templates.TemplateResponse("financial/upcoming_shoots_detail.html", {
            "request": request,
            "page_title": "Upcoming Shoot Details",
            "shoot": shoot,
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        }, status_code=500)
