"""
Monthly Financial Reports routes - Track revenue, expenses, and profit on monthly basis.
"""

from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import MonthlyFinancialReport
from datetime import datetime, date, timedelta
import os
from sqlalchemy import func, extract

router = APIRouter(prefix="/financial/monthly", tags=["Monthly Financial Reports"])

# Setup templates
template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
templates = Jinja2Templates(directory=template_dir)


@router.get("/", response_class=HTMLResponse)
async def list_monthly_reports(request: Request, db: Session = Depends(get_db), month: str = None):
    """List all monthly financial reports with filtering."""
    try:
        query = db.query(MonthlyFinancialReport).order_by(MonthlyFinancialReport.month.desc())
        
        if month:
            query = query.filter(extract('year-month', MonthlyFinancialReport.month) == month)
        
        reports = query.all()
        
        # Calculate totals
        total_revenue = db.query(func.sum(MonthlyFinancialReport.total_amount)).scalar() or 0.0
        total_paid = db.query(func.sum(MonthlyFinancialReport.paid_amount)).scalar() or 0.0
        total_pending = db.query(func.sum(MonthlyFinancialReport.pending_amount)).scalar() or 0.0
        total_expenses = db.query(func.sum(MonthlyFinancialReport.expenses)).scalar() or 0.0
        total_profit = db.query(func.sum(MonthlyFinancialReport.profit)).scalar() or 0.0
        
        return templates.TemplateResponse("financial/monthly_list.html", {
            "request": request,
            "page_title": "Monthly Financial Reports",
            "reports": reports,
            "total_revenue": total_revenue,
            "total_paid": total_paid,
            "total_pending": total_pending,
            "total_expenses": total_expenses,
            "total_profit": total_profit,
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        }, status_code=500)


@router.get("/create", response_class=HTMLResponse)
async def create_form(request: Request):
    """Display form to create new monthly financial report."""
    try:
        # provide current year and month names (values include year for submission)
        current_year = datetime.utcnow().year
        import calendar
        months = [(f"{current_year}-{i:02d}-01", calendar.month_name[i]) for i in range(1, 13)]
        event_types = ["Wedding", "Corporate", "Pre-Wedding", "Birthday", "Other"]

        return templates.TemplateResponse("financial/monthly_form.html", {
            "request": request,
            "page_title": "Create Monthly Financial Report",
            "is_edit": False,
            "months": months,
            "event_types": event_types,
            "current_year": current_year,
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        }, status_code=500)


@router.post("/create")
async def create_report(
    request: Request,
    db: Session = Depends(get_db),
    month: str = Form(...),
    client_name: str = Form(...),
    event_type: str = Form(...),
    event_date: str = Form(...),
    total_amount: float = Form(...),
    paid_amount: float = Form(...),
    freelancer_amount: float = Form(...),
    expenses: float = Form(...),
    payment_status: str = Form(...),
    work_status: str = Form(...),
    notes: str = Form(default=""),
):
    """Create new monthly financial report."""
    try:
        report = MonthlyFinancialReport(
            month=datetime.strptime(month, "%Y-%m-01").date(),
            client_name=client_name,
            event_type=event_type,
            event_date=datetime.strptime(event_date, "%Y-%m-%d").date(),
            total_amount=total_amount,
            paid_amount=paid_amount,
            freelancer_amount=freelancer_amount,
            expenses=expenses,
            payment_status=payment_status,
            work_status=work_status,
            notes=notes,
        )
        report.calculate_pending()
        report.calculate_profit()
        
        db.add(report)
        db.commit()
        
        return RedirectResponse(url="/financial/monthly/", status_code=302)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{report_id}/edit", response_class=HTMLResponse)
async def edit_form(request: Request, report_id: int, db: Session = Depends(get_db)):
    """Display form to edit monthly financial report."""
    try:
        report = db.query(MonthlyFinancialReport).filter(MonthlyFinancialReport.id == report_id).first()
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # provide months and event types for dropdowns
        current_year = datetime.utcnow().year
        import calendar
        months = [(f"{current_year}-{i:02d}-01", calendar.month_name[i]) for i in range(1, 13)]
        # if report's year differs, add the report month value so selection matches
        if report and report.month:
            rep_val = report.month.strftime('%Y-%m-01')
            rep_label = report.month.strftime('%B')
            if rep_val not in [v for v, l in months]:
                months.insert(0, (rep_val, rep_label))

        event_types = ["Wedding", "Corporate", "Pre-Wedding", "Birthday", "Other"]

        return templates.TemplateResponse("financial/monthly_form.html", {
            "request": request,
            "page_title": "Edit Monthly Financial Report",
            "report": report,
            "is_edit": True,
            "months": months,
            "event_types": event_types,
            "current_year": current_year,
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        }, status_code=500)


@router.post("/{report_id}/edit")
async def edit_report(
    report_id: int,
    db: Session = Depends(get_db),
    month: str = Form(...),
    client_name: str = Form(...),
    event_type: str = Form(...),
    event_date: str = Form(...),
    total_amount: float = Form(...),
    paid_amount: float = Form(...),
    freelancer_amount: float = Form(...),
    expenses: float = Form(...),
    payment_status: str = Form(...),
    work_status: str = Form(...),
    notes: str = Form(default=""),
):
    """Update monthly financial report."""
    try:
        report = db.query(MonthlyFinancialReport).filter(MonthlyFinancialReport.id == report_id).first()
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        report.month = datetime.strptime(month, "%Y-%m-01").date()
        report.client_name = client_name
        report.event_type = event_type
        report.event_date = datetime.strptime(event_date, "%Y-%m-%d").date()
        report.total_amount = total_amount
        report.paid_amount = paid_amount
        report.freelancer_amount = freelancer_amount
        report.expenses = expenses
        report.payment_status = payment_status
        report.work_status = work_status
        report.notes = notes
        report.calculate_pending()
        report.calculate_profit()
        
        db.commit()
        return RedirectResponse(url="/financial/monthly/", status_code=302)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{report_id}/delete")
async def delete_report(report_id: int, db: Session = Depends(get_db)):
    """Delete monthly financial report."""
    try:
        report = db.query(MonthlyFinancialReport).filter(MonthlyFinancialReport.id == report_id).first()
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        db.delete(report)
        db.commit()
        
        return RedirectResponse(url="/financial/monthly/", status_code=302)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{report_id}/detail", response_class=HTMLResponse)
async def detail_report(request: Request, report_id: int, db: Session = Depends(get_db)):
    """Display detailed view of a monthly financial report."""
    try:
        report = db.query(MonthlyFinancialReport).filter(MonthlyFinancialReport.id == report_id).first()
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return templates.TemplateResponse("financial/monthly_detail.html", {
            "request": request,
            "page_title": "Monthly Financial Report Details",
            "report": report,
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        }, status_code=500)
