"""
Checklist module routes for managing equipment and role-based checklists.
"""

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Checklist
from datetime import datetime
import os

router = APIRouter(prefix="/checklist", tags=["Checklist"])

# Setup templates
template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
templates = Jinja2Templates(directory=template_dir)


@router.get("/", response_class=HTMLResponse)
async def list_checklists(
    request: Request,
    search: str = None,
    db: Session = Depends(get_db)
):
    """Display list of checklists."""
    try:
        query = db.query(Checklist).order_by(Checklist.created_at.desc())
        
        if search:
            query = query.filter(Checklist.couple_name.ilike(f"%{search}%"))
        
        records = query.all()
        
        context = {
            "request": request,
            "page_title": "Checklists",
            "records": records,
            "search_query": search or "",
        }
        
        return templates.TemplateResponse("checklist/list.html", context)
    
    except Exception as e:
        print(f"Error listing checklists: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": str(e)},
            status_code=500
        )


@router.get("/add", response_class=HTMLResponse)
async def add_checklist_form(request: Request):
    """Display form for adding new checklist."""
    context = {
        "request": request,
        "page_title": "Add Checklist",
    }
    return templates.TemplateResponse("checklist/form.html", context)


@router.post("/add")
async def create_checklist(
    couple_name: str = Form(...),
    event_date: str = Form(...),
    equipments_ready: bool = Form(False),
    equipment_notes: str = Form(None),
    traditional_videographer: bool = Form(False),
    videographer_notes: str = Form(None),
    traditional_photographer: bool = Form(False),
    photographer_notes: str = Form(None),
    candid_photographer: bool = Form(False),
    candid_notes: str = Form(None),
    cinematographer: bool = Form(False),
    cinematographer_notes: str = Form(None),
    drone_shooter: bool = Form(False),
    drone_notes: str = Form(None),
    pre_wedding_shoot: bool = Form(False),
    pre_wedding_notes: str = Form(None),
    assigned_team: str = Form(None),
    checklist_status: str = Form("pending"),
    notes: str = Form(None),
    db: Session = Depends(get_db)
):
    """Create new checklist."""
    try:
        record = Checklist(
            couple_name=couple_name,
            event_date=datetime.strptime(event_date, "%Y-%m-%d").date(),
            equipments_ready=equipments_ready,
            equipment_notes=equipment_notes,
            traditional_videographer=traditional_videographer,
            videographer_notes=videographer_notes,
            traditional_photographer=traditional_photographer,
            photographer_notes=photographer_notes,
            candid_photographer=candid_photographer,
            candid_notes=candid_notes,
            cinematographer=cinematographer,
            cinematographer_notes=cinematographer_notes,
            drone_shooter=drone_shooter,
            drone_notes=drone_notes,
            pre_wedding_shoot=pre_wedding_shoot,
            pre_wedding_notes=pre_wedding_notes,
            assigned_team=assigned_team,
            checklist_status=checklist_status,
            notes=notes,
            created_by="Admin"
        )
        
        db.add(record)
        db.commit()
        
        return RedirectResponse(url="/checklist", status_code=303)
    
    except Exception as e:
        db.rollback()
        print(f"Error creating checklist: {str(e)}")
        raise


@router.get("/{record_id}", response_class=HTMLResponse)
async def view_checklist(
    request: Request,
    record_id: int,
    db: Session = Depends(get_db)
):
    """Display details of a specific checklist."""
    try:
        record = db.query(Checklist).filter(Checklist.id == record_id).first()
        
        if not record:
            return templates.TemplateResponse(
                "error.html",
                {"request": request, "error": "Checklist not found"},
                status_code=404
            )
        
        context = {
            "request": request,
            "page_title": f"Checklist: {record.couple_name}",
            "record": record,
            "completion_percentage": record.get_completion_percentage(),
        }
        
        return templates.TemplateResponse("checklist/detail.html", context)
    
    except Exception as e:
        print(f"Error viewing checklist: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": str(e)},
            status_code=500
        )


@router.get("/{record_id}/edit", response_class=HTMLResponse)
async def edit_checklist_form(
    request: Request,
    record_id: int,
    db: Session = Depends(get_db)
):
    """Display form for editing checklist."""
    try:
        record = db.query(Checklist).filter(Checklist.id == record_id).first()
        
        if not record:
            return templates.TemplateResponse(
                "error.html",
                {"request": request, "error": "Checklist not found"},
                status_code=404
            )
        
        context = {
            "request": request,
            "page_title": f"Edit Checklist: {record.couple_name}",
            "record": record,
        }
        
        return templates.TemplateResponse("checklist/form.html", context)
    
    except Exception as e:
        print(f"Error loading edit form: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": str(e)},
            status_code=500
        )


@router.post("/{record_id}/edit")
async def update_checklist(
    record_id: int,
    couple_name: str = Form(...),
    event_date: str = Form(...),
    equipments_ready: bool = Form(False),
    equipment_notes: str = Form(None),
    traditional_videographer: bool = Form(False),
    videographer_notes: str = Form(None),
    traditional_photographer: bool = Form(False),
    photographer_notes: str = Form(None),
    candid_photographer: bool = Form(False),
    candid_notes: str = Form(None),
    cinematographer: bool = Form(False),
    cinematographer_notes: str = Form(None),
    drone_shooter: bool = Form(False),
    drone_notes: str = Form(None),
    pre_wedding_shoot: bool = Form(False),
    pre_wedding_notes: str = Form(None),
    assigned_team: str = Form(None),
    checklist_status: str = Form("pending"),
    notes: str = Form(None),
    db: Session = Depends(get_db)
):
    """Update checklist."""
    try:
        record = db.query(Checklist).filter(Checklist.id == record_id).first()
        
        if not record:
            return {"error": "Checklist not found"}, 404
        
        record.couple_name = couple_name
        record.event_date = datetime.strptime(event_date, "%Y-%m-%d").date()
        record.equipments_ready = equipments_ready
        record.equipment_notes = equipment_notes
        record.traditional_videographer = traditional_videographer
        record.videographer_notes = videographer_notes
        record.traditional_photographer = traditional_photographer
        record.photographer_notes = photographer_notes
        record.candid_photographer = candid_photographer
        record.candid_notes = candid_notes
        record.cinematographer = cinematographer
        record.cinematographer_notes = cinematographer_notes
        record.drone_shooter = drone_shooter
        record.drone_notes = drone_notes
        record.pre_wedding_shoot = pre_wedding_shoot
        record.pre_wedding_notes = pre_wedding_notes
        record.assigned_team = assigned_team
        record.checklist_status = checklist_status
        record.notes = notes
        record.updated_at = datetime.utcnow()
        
        db.commit()
        
        return RedirectResponse(url=f"/checklist/{record_id}", status_code=303)
    
    except Exception as e:
        db.rollback()
        print(f"Error updating checklist: {str(e)}")
        raise


@router.post("/{record_id}/delete")
async def delete_checklist(
    record_id: int,
    db: Session = Depends(get_db)
):
    """Delete checklist."""
    try:
        record = db.query(Checklist).filter(Checklist.id == record_id).first()
        
        if not record:
            return {"error": "Checklist not found"}, 404
        
        db.delete(record)
        db.commit()
        
        return RedirectResponse(url="/checklist", status_code=303)
    
    except Exception as e:
        db.rollback()
        print(f"Error deleting checklist: {str(e)}")
        raise
