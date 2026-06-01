"""
Clients Editing routes - Track editing workload and revenue.
"""

from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import ClientsEditing
from datetime import datetime, date
import os
from sqlalchemy import func, extract
from .monthly_financial import number_to_words

router = APIRouter(prefix="/financial/editing", tags=["Clients Editing"])

# Setup templates
template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
templates = Jinja2Templates(directory=template_dir)


@router.get("/", response_class=HTMLResponse)
async def list_editing(
    request: Request,
    db: Session = Depends(get_db),
    search: str = None,
    year: str = None,
    month: str = None,
):
    """List all editing projects with analytics."""
    try:
        query = db.query(ClientsEditing).order_by(
            ClientsEditing.date.desc()
        )
        
        if search:
            query = query.filter(ClientsEditing.client_name.ilike(f"%{search}%"))
        if year:
            try:
                query = query.filter(extract('year', ClientsEditing.date) == int(year))
            except ValueError:
                pass
        if month:
            try:
                query = query.filter(extract('month', ClientsEditing.date) == int(month))
            except ValueError:
                pass
        
        editing_projects = query.all()
        
        # Calculate totals for filtered results
        total_revenue = sum(p.total_amount for p in editing_projects) if editing_projects else 0.0
        total_revenue_words = number_to_words(total_revenue)
        pending_count = sum(1 for p in editing_projects if p.work_status == "Pending")
        done_count = sum(1 for p in editing_projects if p.work_status == "Done")
        completion_rate = (done_count / len(editing_projects) * 100) if len(editing_projects) > 0 else 0
        
        # Payment status breakdown
        online_payment = sum(p.total_amount for p in editing_projects if p.payment_status == "Online")
        cash_payment = sum(p.total_amount for p in editing_projects if p.payment_status == "Cash")
        
        return templates.TemplateResponse("financial/editing_list.html", {
            "request": request,
            "page_title": "Clients Editing",
            "projects": editing_projects,
            "total_revenue": total_revenue,
            "total_revenue_words": total_revenue_words,
            "pending_count": pending_count,
            "done_count": done_count,
            "completion_rate": round(completion_rate, 2),
            "online_payment": online_payment,
            "cash_payment": cash_payment,
            "search_query": search or "",
            "selected_year": year or "",
            "selected_month": month or "",
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        }, status_code=500)


@router.get("/create", response_class=HTMLResponse)
async def create_form(request: Request):
    """Display form to create new editing project."""
    try:
        return templates.TemplateResponse("financial/editing_form.html", {
            "request": request,
            "page_title": "Create Editing Project",
            "is_edit": False,
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        }, status_code=500)


@router.post("/create")
async def create_editing(
    request: Request,
    db: Session = Depends(get_db),
    date_input: str = Form(...),
    client_name: str = Form(...),
    editing_type: str = Form(...),
    total_amount: float = Form(...),
    payment_status: str = Form(...),
    work_status: str = Form(...),
    description: str = Form(default=""),
):
    """Create new editing project."""
    try:
        project = ClientsEditing(
            date=datetime.strptime(date_input, "%Y-%m-%d").date(),
            client_name=client_name,
            editing_type=editing_type,
            total_amount=total_amount,
            payment_status=payment_status,
            work_status=work_status,
            description=description,
        )
        
        db.add(project)
        db.commit()
        
        return RedirectResponse(url="/financial/editing/", status_code=302)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{project_id}/edit", response_class=HTMLResponse)
async def edit_form(request: Request, project_id: int, db: Session = Depends(get_db)):
    """Display form to edit editing project."""
    try:
        project = db.query(ClientsEditing).filter(ClientsEditing.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return templates.TemplateResponse("financial/editing_form.html", {
            "request": request,
            "page_title": "Edit Editing Project",
            "project": project,
            "is_edit": True,
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        }, status_code=500)


@router.post("/{project_id}/edit")
async def edit_editing(
    project_id: int,
    db: Session = Depends(get_db),
    date_input: str = Form(...),
    client_name: str = Form(...),
    editing_type: str = Form(...),
    total_amount: float = Form(...),
    payment_status: str = Form(...),
    work_status: str = Form(...),
    description: str = Form(default=""),
):
    """Update editing project."""
    try:
        project = db.query(ClientsEditing).filter(ClientsEditing.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project.date = datetime.strptime(date_input, "%Y-%m-%d").date()
        project.client_name = client_name
        project.editing_type = editing_type
        project.total_amount = total_amount
        project.payment_status = payment_status
        project.work_status = work_status
        project.description = description
        
        db.commit()
        return RedirectResponse(url="/financial/editing/", status_code=302)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{project_id}/delete")
async def delete_editing(project_id: int, db: Session = Depends(get_db)):
    """Delete editing project."""
    try:
        project = db.query(ClientsEditing).filter(ClientsEditing.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        db.delete(project)
        db.commit()
        
        return RedirectResponse(url="/financial/editing/", status_code=302)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{project_id}/detail", response_class=HTMLResponse)
async def detail_editing(request: Request, project_id: int, db: Session = Depends(get_db)):
    """Display detailed view of an editing project."""
    try:
        project = db.query(ClientsEditing).filter(ClientsEditing.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return templates.TemplateResponse("financial/editing_detail.html", {
            "request": request,
            "page_title": "Editing Project Details",
            "project": project,
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        }, status_code=500)
