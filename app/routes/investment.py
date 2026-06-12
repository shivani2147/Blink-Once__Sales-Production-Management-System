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
from .monthly_financial import number_to_words

router = APIRouter(prefix="/financial/investment", tags=["Investment To Grow Company"])

# Setup templates
template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
templates = Jinja2Templates(directory=template_dir)


@router.get("/", response_class=HTMLResponse)
async def list_investments(
    request: Request,
    db: Session = Depends(get_db),
    search: str = None,
    year: str = None,
    month: str = None,
):
    """List all investments with analytics."""
    try:
        query = db.query(InvestmentToGrowCompany).order_by(
            InvestmentToGrowCompany.date.desc()
        )
        
        if search:
            query = query.filter(
                InvestmentToGrowCompany.service.ilike(f"%{search}%") |
                InvestmentToGrowCompany.description.ilike(f"%{search}%")
            )
        if year:
            try:
                query = query.filter(extract('year', InvestmentToGrowCompany.date) == int(year))
            except ValueError:
                pass
        if month:
            try:
                query = query.filter(extract('month', InvestmentToGrowCompany.date) == int(month))
            except ValueError:
                pass
        
        investments = query.all()
        
        # Calculate totals for filtered results
        total_amount_sum = sum(i.total_amount for i in investments if not i.payment_status or i.payment_status == 'Done') if investments else 0.0
        pending_amount_sum = sum(i.pending_amount for i in investments) if investments else 0.0
        investment_count = len(investments)
        
        total_amount_sum_words = number_to_words(total_amount_sum)
        pending_amount_sum_words = number_to_words(pending_amount_sum)
        
        # Service-wise breakdown
        service_stats = {}
        for investment in investments:
            if investment.service not in service_stats:
                service_stats[investment.service] = {"count": 0, "amount": 0.0}
            service_stats[investment.service]["count"] += 1
            service_stats[investment.service]["amount"] += investment.total_amount
        
        return templates.TemplateResponse("financial/investment_list.html", {
            "request": request,
            "page_title": "Investment To Grow Company",
            "investments": investments,
            "total_amount_sum": total_amount_sum,
            "total_amount_sum_words": total_amount_sum_words,
            "pending_amount_sum": pending_amount_sum,
            "pending_amount_sum_words": pending_amount_sum_words,
            "investment_count": investment_count,
            "service_stats": service_stats,
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
    total_amount: float = Form(...),
    paid_amount: float = Form(default=0.0),
    pending_amount: float = Form(default=0.0),
    payment_mode: str = Form(default="Cash"),
    payment_status: str = Form(default="Done"),
    description: str = Form(default=""),
):
    """Create new investment."""
    try:
        investment = InvestmentToGrowCompany(
            date=datetime.strptime(date_input, "%Y-%m-%d").date(),
            service=service,
            total_amount=total_amount,
            paid_amount=paid_amount,
            pending_amount=pending_amount,
            payment_mode=payment_mode,
            payment_status=payment_status,
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
    total_amount: float = Form(...),
    paid_amount: float = Form(default=0.0),
    pending_amount: float = Form(default=0.0),
    payment_mode: str = Form(default="Cash"),
    payment_status: str = Form(default="Done"),
    description: str = Form(default=""),
):
    """Update investment with comma-separated amount handling."""
    try:
        investment = db.query(InvestmentToGrowCompany).filter(
            InvestmentToGrowCompany.id == investment_id
        ).first()
        if not investment:
            raise HTTPException(status_code=404, detail="Investment not found")

        investment.date = datetime.strptime(date_input, "%Y-%m-%d").date()
        investment.service = service
        investment.total_amount = total_amount
        investment.paid_amount = paid_amount
        investment.pending_amount = pending_amount
        investment.payment_mode = payment_mode
        investment.payment_status = payment_status
        investment.description = description

        db.commit()
        return RedirectResponse(url="/financial/investment/", status_code=302)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# @router.get("/{investment_id}/delete")
# async def delete_investment(investment_id: int, db: Session = Depends(get_db)):
#     """Delete investment."""
#     try:
#         investment = db.query(InvestmentToGrowCompany).filter(
#             InvestmentToGrowCompany.id == investment_id
#         ).first()
#         if not investment:
#             raise HTTPException(status_code=404, detail="Investment not found")
        
#         db.delete(investment)
#         db.commit()
        
#         return RedirectResponse(url="/financial/investment/", status_code=302)
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))

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
