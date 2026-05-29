"""
Investment To Grow Company routes - Track investments and expenses.
"""

from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import InvestmentToGrowCompany
from datetime import datetime, date
import os
from sqlalchemy import func, extract

router = APIRouter(prefix="/financial/investment", tags=["Investment To Grow Company"])

# Setup templates
template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
templates = Jinja2Templates(directory=template_dir)


@router.get("/", response_class=HTMLResponse)
async def list_investments(request: Request, db: Session = Depends(get_db)):
    """List all investments with analytics."""
    try:
        investments = db.query(InvestmentToGrowCompany).order_by(
            InvestmentToGrowCompany.date.desc()
        ).all()
        
        # Calculate totals
        total_investment = db.query(func.sum(InvestmentToGrowCompany.amount)).scalar() or 0.0
        total_amount_sum = db.query(func.sum(InvestmentToGrowCompany.total_amount)).scalar() or 0.0
        investment_count = len(investments)
        
        # Service-wise breakdown
        service_stats = {}
        for investment in investments:
            if investment.service not in service_stats:
                service_stats[investment.service] = {"count": 0, "amount": 0.0}
            service_stats[investment.service]["count"] += 1
            service_stats[investment.service]["amount"] += investment.amount
        
        return templates.TemplateResponse("financial/investment_list.html", {
            "request": request,
            "page_title": "Investment To Grow Company",
            "investments": investments,
            "total_investment": total_investment,
            "total_amount_sum": total_amount_sum,
            "investment_count": investment_count,
            "service_stats": service_stats,
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        }, status_code=500)


@router.get("/create", response_class=HTMLResponse)
async def create_form(request: Request):
    """Display form to create new investment."""
    try:
        return templates.TemplateResponse("financial/investment_form.html", {
            "request": request,
            "page_title": "Create Investment",
            "is_edit": False,
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        }, status_code=500)


@router.post("/create")
async def create_investment(
    request: Request,
    db: Session = Depends(get_db),
    date_input: str = Form(...),
    service: str = Form(...),
    amount: float = Form(...),
    total_amount: float = Form(...),
    description: str = Form(default=""),
):
    """Create new investment."""
    try:
        investment = InvestmentToGrowCompany(
            date=datetime.strptime(date_input, "%Y-%m-%d").date(),
            service=service,
            amount=amount,
            total_amount=total_amount,
            description=description,
        )
        
        db.add(investment)
        db.commit()
        
        return RedirectResponse(url="/financial/investment/", status_code=302)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{investment_id}/edit", response_class=HTMLResponse)
async def edit_form(request: Request, investment_id: int, db: Session = Depends(get_db)):
    """Display form to edit investment."""
    try:
        investment = db.query(InvestmentToGrowCompany).filter(
            InvestmentToGrowCompany.id == investment_id
        ).first()
        if not investment:
            raise HTTPException(status_code=404, detail="Investment not found")
        
        return templates.TemplateResponse("financial/investment_form.html", {
            "request": request,
            "page_title": "Edit Investment",
            "investment": investment,
            "is_edit": True,
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        }, status_code=500)


@router.post("/{investment_id}/edit")
async def edit_investment(
    investment_id: int,
    db: Session = Depends(get_db),
    date_input: str = Form(...),
    service: str = Form(...),
    amount: float = Form(...),
    total_amount: float = Form(...),
    description: str = Form(default=""),
):
    """Update investment."""
    try:
        investment = db.query(InvestmentToGrowCompany).filter(
            InvestmentToGrowCompany.id == investment_id
        ).first()
        if not investment:
            raise HTTPException(status_code=404, detail="Investment not found")
        
        investment.date = datetime.strptime(date_input, "%Y-%m-%d").date()
        investment.service = service
        investment.amount = amount
        investment.total_amount = total_amount
        investment.description = description
        
        db.commit()
        return RedirectResponse(url="/financial/investment/", status_code=302)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{investment_id}/delete")
async def delete_investment(investment_id: int, db: Session = Depends(get_db)):
    """Delete investment."""
    try:
        investment = db.query(InvestmentToGrowCompany).filter(
            InvestmentToGrowCompany.id == investment_id
        ).first()
        if not investment:
            raise HTTPException(status_code=404, detail="Investment not found")
        
        db.delete(investment)
        db.commit()
        
        return RedirectResponse(url="/financial/investment/", status_code=302)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{investment_id}/detail", response_class=HTMLResponse)
async def detail_investment(request: Request, investment_id: int, db: Session = Depends(get_db)):
    """Display detailed view of an investment."""
    try:
        investment = db.query(InvestmentToGrowCompany).filter(
            InvestmentToGrowCompany.id == investment_id
        ).first()
        if not investment:
            raise HTTPException(status_code=404, detail="Investment not found")
        
        return templates.TemplateResponse("financial/investment_detail.html", {
            "request": request,
            "page_title": "Investment Details",
            "investment": investment,
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        }, status_code=500)
