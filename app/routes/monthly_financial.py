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
import calendar
from sqlalchemy import func, extract, case

router = APIRouter(prefix="/financial/monthly", tags=["Monthly Financial Reports"])

def number_to_words(amount: float) -> str:
    try:
        value = int(round(amount or 0))
    except Exception:
        return "zero rupees"

    if value == 0:
        return "zero rupees"

    ones = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
    tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
    scales = [(10000000, "crore"), (100000, "lakh"), (1000, "thousand"), (100, "hundred")]

    def int_to_words(n: int) -> str:
        if n < 20:
            return ones[n]
        if n < 100:
            return tens[n // 10] + (" " + ones[n % 10] if n % 10 else "")
        for scale_value, scale_name in scales:
            if n >= scale_value:
                quotient, remainder = divmod(n, scale_value)
                result = int_to_words(quotient) + " " + scale_name
                if remainder:
                    result += " " + int_to_words(remainder)
                return result
        return ""

    return int_to_words(value) + " rupees"

# Setup templates
template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
templates = Jinja2Templates(directory=template_dir)


@router.get("/", response_class=HTMLResponse)
async def list_monthly_reports(
    request: Request,
    db: Session = Depends(get_db),
    search: str = None,
    year: str = None,
    month: str = None,
):
    """List all monthly financial reports with filtering."""
    try:
        month_order = case(
            (MonthlyFinancialReport.month == 'January', 1),
            (MonthlyFinancialReport.month == 'February', 2),
            (MonthlyFinancialReport.month == 'March', 3),
            (MonthlyFinancialReport.month == 'April', 4),
            (MonthlyFinancialReport.month == 'May', 5),
            (MonthlyFinancialReport.month == 'June', 6),
            (MonthlyFinancialReport.month == 'July', 7),
            (MonthlyFinancialReport.month == 'August', 8),
            (MonthlyFinancialReport.month == 'September', 9),
            (MonthlyFinancialReport.month == 'October', 10),
            (MonthlyFinancialReport.month == 'November', 11),
            (MonthlyFinancialReport.month == 'December', 12),
            else_=99
        )
        query = db.query(MonthlyFinancialReport).order_by(
            MonthlyFinancialReport.year.asc(), month_order.asc()
        )
        
        if search:
            query = query.filter(MonthlyFinancialReport.client_name.ilike(f"%{search}%"))
        
        if year:
            try:
                query = query.filter(MonthlyFinancialReport.year == int(year))
            except ValueError:
                pass
        
        if month:
            import calendar
            month_name = month
            if month.isdigit():
                month_num = int(month)
                if 1 <= month_num <= 12:
                    month_name = calendar.month_name[month_num]
            query = query.filter(MonthlyFinancialReport.month == month_name)
        
        reports = query.all()
        
        # Calculate totals for filtered results
        # Total Revenue is the sum of Paid amounts
        total_revenue = sum(r.paid_amount for r in reports) if reports else 0.0
        total_paid = sum(r.paid_amount for r in reports) if reports else 0.0
        total_pending = sum(r.pending_amount for r in reports) if reports else 0.0
        total_expenses = sum(r.expenses + r.freelancer_amount for r in reports) if reports else 0.0
        total_profit = sum(r.profit for r in reports) if reports else 0.0
        
        return templates.TemplateResponse("financial/monthly_list.html", {
            "request": request,
            "page_title": "Monthly Financial Reports",
            "reports": reports,
            "total_revenue": total_revenue,
            "total_revenue_words": number_to_words(total_revenue),
            "total_paid": total_paid,
            "total_pending": total_pending,
            "total_pending_words": number_to_words(total_pending),
            "total_expenses": total_expenses,
            "total_expenses_words": number_to_words(total_expenses),
            "total_profit": total_profit,
            "total_profit_words": number_to_words(total_profit),
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
async def create_form(request: Request, db: Session = Depends(get_db)):
    """Display form to create new monthly financial report."""
    try:
        # provide current year and month names for dropdowns
        current_year = datetime.utcnow().year
        import calendar
        years = list(range(2020, current_year + 1))
        months = [(calendar.month_name[i], calendar.month_name[i]) for i in range(1, 13)]
        event_types = ["Wedding", "Corporate", "Pre-Wedding", "Birthday", "Other"]

        
        from app.routes.freelancers import get_all_project_names
        return templates.TemplateResponse("financial/monthly_form.html", {
            "request": request,
            "page_title": "Create Monthly Financial Report",
            "is_edit": False,
            "months": months,
            "years": years,
            "event_types": event_types,
            "current_year": current_year,
            "all_project_names": get_all_project_names(db),
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
    year: int = Form(...),
    month: str = Form(...),
    client_name: str = Form(...),
    project_name: str = Form(default=""),
    event_type: str = Form(...),
    event_date: str = Form(...),
    total_amount: float = Form(...),
    paid_amount: float = Form(...),
    freelancer_amount: float = Form(default=0.0),
    expenses: float = Form(default=0.0),
    payment_status: str = Form(...),
    work_status: str = Form(...),
    notes: str = Form(default=""),
):
    """Create new monthly financial report."""
    try:
        # Normalize event_date to day numbers
        days = []
        if event_date:
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
        event_date_str = ", ".join(days)

        report = MonthlyFinancialReport(
            month=month,
            year=year,
            client_name=client_name,
            project_name=project_name,
            event_type=event_type,
            event_date=event_date_str,
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
        years = list(range(2020, current_year + 1))
        if report and report.year not in years:
            years.insert(0, report.year)
        months = [(calendar.month_name[i], calendar.month_name[i]) for i in range(1, 13)]

        event_types = ["Wedding", "Corporate", "Pre-Wedding", "Birthday", "Other"]

        from app.routes.freelancers import get_all_project_names
        return templates.TemplateResponse("financial/monthly_form.html", {
            "request": request,
            "page_title": "Edit Monthly Financial Report",
            "report": report,
            "is_edit": True,
            "years": years,
            "months": months,
            "event_types": event_types,
            "current_year": current_year,
            "all_project_names": get_all_project_names(db),
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
    year: int = Form(...),
    month: str = Form(...),
    client_name: str = Form(...),
    project_name: str = Form(default=""),
    event_type: str = Form(...),
    event_date: str = Form(...),
    total_amount: float = Form(...),
    paid_amount: float = Form(...),
    freelancer_amount: float = Form(default=0.0),
    expenses: float = Form(default=0.0),
    payment_status: str = Form(...),
    work_status: str = Form(...),
    notes: str = Form(default=""),
):
    """Update monthly financial report."""
    try:
        report = db.query(MonthlyFinancialReport).filter(MonthlyFinancialReport.id == report_id).first()
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Normalize event_date to day numbers
        days = []
        if event_date:
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
        event_date_str = ", ".join(days)

        report.year = year
        report.month = month
        report.client_name = client_name
        report.project_name = project_name
        report.event_type = event_type
        report.event_date = event_date_str
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
