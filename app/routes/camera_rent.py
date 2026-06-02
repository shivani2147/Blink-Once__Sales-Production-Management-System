"""
Camera Rent routes - Track rental income and equipment usage.
"""

from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import CameraRent
from datetime import datetime, date
import os
from sqlalchemy import func, extract
from decimal import Decimal
from app.utils.number_to_words import number_to_words

router = APIRouter(prefix="/financial/camera-rent", tags=["Camera Rent"])

# Setup templates
template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
templates = Jinja2Templates(directory=template_dir)


@router.get("/", response_class=HTMLResponse)
async def list_camera_rent(
    request: Request,
    db: Session = Depends(get_db),
    search: str = None,
    year: str = None,
    month: str = None,
):
    """List all camera rentals with analytics."""
    try:
        query = db.query(CameraRent).order_by(CameraRent.date.desc())
        
        if search:
            query = query.filter(CameraRent.client_name.ilike(f"%{search}%"))
        if year:
            try:
                query = query.filter(extract('year', CameraRent.date) == int(year))
            except ValueError:
                pass
        if month:
            try:
                query = query.filter(extract('month', CameraRent.date) == int(month))
            except ValueError:
                pass
        
        rentals = query.all()
        
        # Calculate totals for filtered results
        # Total Rental Income should include only rentals where work_status == 'Done'
        total_rental_income = sum(r.total_amount or 0 for r in rentals if r.work_status == "Done") if rentals else Decimal('0.0')
        total_days_rented = sum(r.days for r in rentals) if rentals else 0
        paid_count = sum(1 for r in rentals if r.payment_status in ("Online", "Cash"))
        pending_payments = sum(r.total_amount or 0 for r in rentals if r.work_status != "Done")
        
        total_rental_income_words = number_to_words(total_rental_income)
        pending_payments_words = number_to_words(pending_payments)
        
        return templates.TemplateResponse("financial/camera_rent_list.html", {
            "request": request,
            "page_title": "Camera Rent",
            "rentals": rentals,
            "total_rental_income": total_rental_income,
            "total_rental_income_words": total_rental_income_words,
            "total_days_rented": total_days_rented,
            "rental_count": len(rentals),
            "pending_payments": pending_payments,
            "pending_payments_words": pending_payments_words,
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
    """Display form to create new camera rent."""
    try:
        return templates.TemplateResponse("financial/camera_rent_form.html", {
            "request": request,
            "page_title": "Create Camera Rent",
            "is_edit": False,
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        }, status_code=500)


@router.post("/create")
async def create_rental(
    request: Request,
    db: Session = Depends(get_db),
    date_input: str = Form(...),
    client_name: str = Form(...),
    description_of_goods: str = Form(...),
    days: int = Form(...),
    phone_number: str = Form(...),
    aadhar_card_no: str = Form(default=""),
    total_amount: Decimal = Form(...),
    payment_status: str = Form(...),
    work_status: str = Form(...),
    description: str = Form(default=""),
):
    """Create new camera rent."""
    try:
        # Validate date format
        parsed_date = datetime.strptime(date_input, "%Y-%m-%d").date()
        rental = CameraRent(
            date=parsed_date,
            client_name=client_name,
            description_of_goods=description_of_goods,
            days=days,
            phone_number=phone_number,
            aadhar_card_no=aadhar_card_no,
            total_amount=total_amount,
            payment_status=payment_status,
            work_status=work_status,
            description=description,
        )
        
        db.add(rental)
        db.commit()
        
        return RedirectResponse(url="/financial/camera-rent/", status_code=302)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{rental_id}/edit", response_class=HTMLResponse)
async def edit_form(request: Request, rental_id: int, db: Session = Depends(get_db)):
    """Display form to edit camera rent."""
    try:
        rental = db.query(CameraRent).filter(CameraRent.id == rental_id).first()
        if not rental:
            raise HTTPException(status_code=404, detail="Rental not found")
        
        return templates.TemplateResponse("financial/camera_rent_form.html", {
            "request": request,
            "page_title": "Edit Camera Rent",
            "rental": rental,
            "is_edit": True,
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        }, status_code=500)


@router.post("/{rental_id}/edit")
async def edit_rental(
    rental_id: int,
    db: Session = Depends(get_db),
    date_input: str = Form(...),
    client_name: str = Form(...),
    description_of_goods: str = Form(...),
    days: int = Form(...),
    phone_number: str = Form(...),
    aadhar_card_no: str = Form(default=""),
    total_amount: Decimal = Form(...),
    payment_status: str = Form(...),
    work_status: str = Form(...),
    description: str = Form(default=""),
):
    """Update camera rent."""
    try:
        rental = db.query(CameraRent).filter(CameraRent.id == rental_id).first()
        if not rental:
            raise HTTPException(status_code=404, detail="Rental not found")
        
        # Validate date format
        parsed_date = datetime.strptime(date_input, "%Y-%m-%d").date()
        rental.date = parsed_date
        rental.client_name = client_name
        rental.description_of_goods = description_of_goods
        rental.days = days
        rental.phone_number = phone_number
        rental.aadhar_card_no = aadhar_card_no
        rental.total_amount = total_amount
        rental.payment_status = payment_status
        rental.work_status = work_status
        rental.description = description
        
        db.commit()
        return RedirectResponse(url="/financial/camera-rent/", status_code=302)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{rental_id}/delete")
async def delete_rental(rental_id: int, db: Session = Depends(get_db)):
    """Delete camera rent."""
    try:
        rental = db.query(CameraRent).filter(CameraRent.id == rental_id).first()
        if not rental:
            raise HTTPException(status_code=404, detail="Rental not found")
        
        db.delete(rental)
        db.commit()
        
        return RedirectResponse(url="/financial/camera-rent/", status_code=302)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{rental_id}/detail", response_class=HTMLResponse)
async def detail_rental(request: Request, rental_id: int, db: Session = Depends(get_db)):
    """Display detailed view of a camera rent."""
    try:
        rental = db.query(CameraRent).filter(CameraRent.id == rental_id).first()
        if not rental:
            raise HTTPException(status_code=404, detail="Rental not found")
        
        return templates.TemplateResponse("financial/camera_rent_detail.html", {
            "request": request,
            "page_title": "Camera Rent Details",
            "rental": rental,
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        }, status_code=500)
