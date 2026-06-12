"""
Freelancers module routes for managing freelancer profiles, assignments, and payments.
"""

from fastapi import APIRouter, Depends, Request, Form, HTTPException, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, and_
from app.database import get_db
from app.models import Freelancer, FreelancerWork, PreProduction, OnProduction, PostProduction, MonthlyFinancialReport
from app.config import UPLOAD_DIR, ALLOWED_EXTENSIONS
from app.routes.monthly_financial import number_to_words
from datetime import datetime, date
import os
import uuid
import calendar

router = APIRouter(prefix="/freelancers", tags=["Freelancers"])

# Setup templates
template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
templates = Jinja2Templates(directory=template_dir)

def save_uploaded_file(file: UploadFile):
    """Save uploaded file to upload directory and return filename."""
    if not file or not file.filename:
        return None
    
    # Get file extension
    ext = file.filename.split('.')[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File extension '.{ext}' not allowed.")
    
    # Generate unique filename
    filename = f"{uuid.uuid4().hex}_{file.filename}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    # Write file
    with open(filepath, "wb") as f:
        content = file.file.read()
        f.write(content)
        
    return filename

def delete_file(filename: str):
    """Delete a file from the upload directory."""
    if filename:
        filepath = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                print(f"Error deleting file {filepath}: {e}")

def get_all_project_names(db: Session):
    """Retrieve distinct project names from across modules."""
    _all_names = set()
    for c in db.query(PreProduction.couple_name).distinct().all():
        if c[0]: _all_names.add(c[0])
    for c in db.query(OnProduction.couple_name).distinct().all():
        if c[0]: _all_names.add(c[0])
    for c in db.query(PostProduction.couple_name).distinct().all():
        if c[0]: _all_names.add(c[0])
    for c in db.query(MonthlyFinancialReport.project_name).distinct().all():
        if c[0]: _all_names.add(c[0])
    for c in db.query(FreelancerWork.project_name).distinct().all():
        if c[0]: _all_names.add(c[0])
    return sorted(_all_names)

from fastapi import Query
@router.get("/api/project_amount")
async def get_project_amount(project_name: str = Query(...), db: Session = Depends(get_db)):
    """Get the sum of amount_charged for all FreelancerWork records linked to the given project_name."""
    try:
        total = db.query(func.sum(FreelancerWork.total_amount)).filter(FreelancerWork.project_name == project_name).scalar() or 0.0
        return {"total_amount": float(total)}
    except Exception as e:
        print(f"Error in project amount api: {e}")
        return {"total_amount": 0.0}

@router.get("/", response_class=HTMLResponse)
async def list_freelancers(
    request: Request,
    search: str = None,
    role: str = None,
    status: str = None,
    year: str = None,
    month: str = None,
    db: Session = Depends(get_db)
):
    """List freelancers, search, filter, show metrics, and render analytics charts."""
    try:
        # Base query for directory listing
        query = db.query(Freelancer)
        
        # Apply filters
        if search:
            query = query.filter(
                (Freelancer.name.ilike(f"%{search}%")) |
                (Freelancer.freelancer_id.ilike(f"%{search}%")) |
                (Freelancer.email.ilike(f"%{search}%")) |
                (Freelancer.phone_number.ilike(f"%{search}%")) |
                (Freelancer.remarks.ilike(f"%{search}%"))
            )
        if role:
            query = query.filter(Freelancer.role == role)
        if status:
            query = query.filter(Freelancer.status == status)
            
        freelancers = query.order_by(Freelancer.name.asc()).all()
        
        # Get unique roles for dropdowns
        all_roles = [r[0] for r in db.query(Freelancer.role).distinct().all() if r[0]]
        if not all_roles:
            all_roles = ["Photographer", "Videographer", "Editor", "Cinematographer", "Drone Operator", "Designer"]

        # ============================================
        # YEAR / MONTH FILTER SETUP
        # ============================================
        # Build years_list dynamically from FreelancerWork dates
        years_set = set()
        for row in db.query(extract('year', FreelancerWork.work_date)).distinct().all():
            if row[0]:
                years_set.add(int(row[0]))
        # Always include current year as a fallback
        current_year = datetime.now().year
        years_set.add(current_year)
        years_list = sorted(list(years_set), reverse=True)

        # Standard months mapping
        months_list = [(i, calendar.month_name[i]) for i in range(1, 13)]

        selected_year = year if year else str(current_year)
        selected_month = month if month else "all"

        y_filter_val = None
        if selected_year != "all":
            try:
                y_filter_val = int(selected_year)
            except ValueError:
                pass

        m_filter_val = None
        if selected_month != "all":
            try:
                m_filter_val = int(selected_month)
            except ValueError:
                pass

        selected_month_name = calendar.month_name[m_filter_val] if m_filter_val else "All"

        # Build a base analytics query with optional year/month filters
        def apply_date_filter(q):
            if y_filter_val:
                q = q.filter(extract('year', FreelancerWork.work_date) == y_filter_val)
            if m_filter_val:
                q = q.filter(extract('month', FreelancerWork.work_date) == m_filter_val)
            return q

        # ============================================
        # SUMMARY METRICS (unfiltered totals)
        # ============================================
        total_freelancers = db.query(Freelancer).count()
        active_freelancers = db.query(Freelancer).filter(Freelancer.status == "Active").count()
        inactive_freelancers = db.query(Freelancer).filter(Freelancer.status == "Inactive").count()
        
        total_payments_made = db.query(func.sum(FreelancerWork.amount_charged))\
            .filter(FreelancerWork.payment_status == "Paid").scalar() or 0.0
        pending_payments = db.query(func.sum(FreelancerWork.amount_charged))\
            .filter(FreelancerWork.payment_status == "Pending").scalar() or 0.0
            
        # ============================================
        # ANALYTICS CALCULATIONS (filtered by year/month)
        # ============================================
        
        # 1. Freelancer-wise Earnings (Top Earners)
        earnings_q = db.query(
            Freelancer.name,
            func.sum(FreelancerWork.amount_charged).label('total_earnings')
        ).join(FreelancerWork, Freelancer.id == FreelancerWork.freelancer_id)\
         .filter(FreelancerWork.payment_status == "Paid")
        earnings_q = apply_date_filter(earnings_q)
        freelancer_earnings = earnings_q\
            .group_by(Freelancer.name)\
            .order_by(func.sum(FreelancerWork.amount_charged).desc())\
            .limit(10).all()
         
        earning_labels = [fe[0] for fe in freelancer_earnings]
        earning_values = [float(fe[1] or 0) for fe in freelancer_earnings]
        
        # 2. Role-wise Distribution (unfiltered — always show all freelancers)
        role_dist = db.query(
            Freelancer.role,
            func.count(Freelancer.id).label('count')
        ).group_by(Freelancer.role).all()
        
        role_labels = [rd[0] for rd in role_dist]
        role_values = [int(rd[1] or 0) for rd in role_dist]
        
        # 3. Monthly / Daily Payment Trends (filtered)
        monthly_labels = []
        monthly_values = []

        if y_filter_val and m_filter_val:
            # Day-wise trend for selected month
            last_day = calendar.monthrange(y_filter_val, m_filter_val)[1]
            daily_totals = {d: 0.0 for d in range(1, last_day + 1)}
            
            day_trends = db.query(
                extract('day', FreelancerWork.work_date).label('day'),
                func.sum(FreelancerWork.amount_charged).label('total_amount')
            ).filter(
                FreelancerWork.payment_status == "Paid",
                extract('year', FreelancerWork.work_date) == y_filter_val,
                extract('month', FreelancerWork.work_date) == m_filter_val
            ).group_by(extract('day', FreelancerWork.work_date)).all()
            
            for row in day_trends:
                day_num = int(row.day)
                daily_totals[day_num] = float(row.total_amount or 0)
            
            monthly_labels = [str(d) for d in range(1, last_day + 1)]
            monthly_values = [daily_totals[d] for d in range(1, last_day + 1)]

        elif y_filter_val:
            # Month-wise trend for selected year
            month_totals = {m: 0.0 for m in range(1, 13)}
            
            month_trends = db.query(
                extract('month', FreelancerWork.work_date).label('month'),
                func.sum(FreelancerWork.amount_charged).label('total_amount')
            ).filter(
                FreelancerWork.payment_status == "Paid",
                extract('year', FreelancerWork.work_date) == y_filter_val
            ).group_by(extract('month', FreelancerWork.work_date)).all()
            
            for row in month_trends:
                month_totals[int(row.month)] = float(row.total_amount or 0)
            
            monthly_labels = [calendar.month_name[m] for m in range(1, 13)]
            monthly_values = [month_totals[m] for m in range(1, 13)]

        else:
            # All-time: group by year+month
            all_trends = db.query(
                extract('year', FreelancerWork.work_date).label('year'),
                extract('month', FreelancerWork.work_date).label('month'),
                func.sum(FreelancerWork.amount_charged).label('total_amount')
            ).filter(FreelancerWork.payment_status == "Paid")\
             .group_by(
                 extract('year', FreelancerWork.work_date),
                 extract('month', FreelancerWork.work_date)
             ).order_by(
                 extract('year', FreelancerWork.work_date),
                 extract('month', FreelancerWork.work_date)
             ).all()
            
            for t in all_trends:
                yr = int(t.year)
                m_num = int(t.month)
                monthly_labels.append(f"{calendar.month_abbr[m_num]} {yr}")
                monthly_values.append(float(t.total_amount or 0))
            
            # Fallback if no records found
            if not monthly_labels:
                now = datetime.now()
                for i in range(5, -1, -1):
                    prev_month = now.month - i
                    prev_year = now.year
                    if prev_month <= 0:
                        prev_month += 12
                        prev_year -= 1
                    monthly_labels.append(f"{calendar.month_abbr[prev_month]} {prev_year}")
                    monthly_values.append(0.0)

        context = {
            "request": request,
            "page_title": "Freelancers Directory",
            "freelancers": freelancers,
            "all_roles": all_roles,
            "search_query": search or "",
            "selected_role": role or "",
            "selected_status": status or "",
            
            # Year / Month filter context
            "years_list": years_list,
            "months_list": months_list,
            "selected_year": selected_year,
            "selected_month": selected_month,
            "selected_month_name": selected_month_name,

            # Summary Metrics
            "total_freelancers": total_freelancers,
            "active_freelancers": active_freelancers,
            "inactive_freelancers": inactive_freelancers,
            "total_payments_made": total_payments_made,
            "total_payments_made_words": number_to_words(total_payments_made),
            "pending_payments": pending_payments,
            "pending_payments_words": number_to_words(pending_payments),
            
            # Analytics Data (JSON lists)
            "earning_labels": earning_labels,
            "earning_values": earning_values,
            "role_labels": role_labels,
            "role_values": role_values,
            "monthly_labels": monthly_labels,
            "monthly_values": monthly_values,
        }
        
        return templates.TemplateResponse("freelancers/list.html", context)
        
    except Exception as e:
        print(f"Error loading freelancers list: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": str(e)},
            status_code=500
        )


@router.get("/add", response_class=HTMLResponse)
async def add_freelancer_form(request: Request):
    """Display form for adding new freelancer."""
    roles = ["Photographer", "Videographer", "Editor", "Cinematographer", "Drone Operator", "Designer", "Other"]
    context = {
        "request": request,
        "page_title": "Add New Freelancer",
        "roles": roles,
        "is_edit": False
    }
    return templates.TemplateResponse("freelancers/form.html", context)


@router.post("/add")
async def create_freelancer(
    name: str = Form(...),
    phone_number: str = Form(...),
    email: str = Form(...),
    address: str = Form(None),
    role: str = Form(...),
    per_day_charge: float = Form(0.0),
    per_project_charge: float = Form(0.0),
    bank_name: str = Form(None),
    account_number: str = Form(None),
    ifsc_code: str = Form(None),
    upi_id: str = Form(None),
    pan_number: str = Form(None),
    aadhar_number: str = Form(None),
    status: str = Form("Active"),
    remarks: str = Form(None),
    aadhar_card: UploadFile = File(None),
    resume: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    """Create a new freelancer profile and save uploaded documents."""
    try:
        # Save documents if uploaded
        aadhar_card_filename = save_uploaded_file(aadhar_card)
        resume_filename = save_uploaded_file(resume)
        
        # Auto-generate Freelancer ID
        max_id = db.query(func.max(Freelancer.id)).scalar() or 0
        next_id = max_id + 1
        freelancer_id = f"FL{next_id:04d}"
        
        record = Freelancer(
            freelancer_id=freelancer_id,
            name=name,
            phone_number=phone_number,
            email=email,
            address=address,
            role=role,
            per_day_charge=per_day_charge,
            per_project_charge=per_project_charge,
            bank_name=bank_name,
            account_number=account_number,
            ifsc_code=ifsc_code,
            upi_id=upi_id,
            pan_number=pan_number,
            aadhar_number=aadhar_number,
            status=status,
            remarks=remarks,
            aadhar_card_path=aadhar_card_filename,
            resume_path=resume_filename
        )
        
        db.add(record)
        db.commit()
        db.refresh(record)
        
        return RedirectResponse(url=f"/freelancers/{record.id}", status_code=303)
        
    except Exception as e:
        db.rollback()
        print(f"Error creating freelancer: {str(e)}")
        raise


@router.get("/{freelancer_id}", response_class=HTMLResponse)
async def view_freelancer_profile(
    request: Request,
    freelancer_id: int,
    db: Session = Depends(get_db)
):
    """Display freelancer details, work assignments, and payments history."""
    try:
        freelancer = db.query(Freelancer).filter(Freelancer.id == freelancer_id).first()
        if not freelancer:
            return templates.TemplateResponse(
                "error.html",
                {"request": request, "error": "Freelancer profile not found"},
                status_code=404
            )
            
        # Fetch work assignments
        assignments = db.query(FreelancerWork)\
            .filter(FreelancerWork.freelancer_id == freelancer.id)\
            .order_by(FreelancerWork.work_date.desc()).all()
            
        # Calculate statistics
        total_earned = sum(a.amount_charged for a in assignments if a.payment_status == "Paid")
        total_pending = sum(a.amount_charged for a in assignments if a.payment_status == "Pending")
        total_assignments = len(assignments)
        
        context = {
            "request": request,
            "page_title": f"Profile: {freelancer.name}",
            "freelancer": freelancer,
            "assignments": assignments,
            "total_earned": total_earned,
            "total_earned_words": number_to_words(total_earned),
            "total_pending": total_pending,
            "total_pending_words": number_to_words(total_pending),
            "total_assignments": total_assignments
        }
        
        return templates.TemplateResponse("freelancers/profile.html", context)
        
    except Exception as e:
        print(f"Error viewing freelancer profile: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": str(e)},
            status_code=500
        )


@router.get("/{freelancer_id}/edit", response_class=HTMLResponse)
async def edit_freelancer_form(
    request: Request,
    freelancer_id: int,
    db: Session = Depends(get_db)
):
    """Display edit freelancer profile form."""
    try:
        freelancer = db.query(Freelancer).filter(Freelancer.id == freelancer_id).first()
        if not freelancer:
            return templates.TemplateResponse(
                "error.html",
                {"request": request, "error": "Freelancer profile not found"},
                status_code=404
            )
            
        roles = ["Photographer", "Videographer", "Editor", "Cinematographer", "Drone Operator", "Designer", "Other"]
        context = {
            "request": request,
            "page_title": f"Edit Profile: {freelancer.name}",
            "freelancer": freelancer,
            "roles": roles,
            "is_edit": True
        }
        
        return templates.TemplateResponse("freelancers/form.html", context)
        
    except Exception as e:
        print(f"Error loading freelancer edit form: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": str(e)},
            status_code=500
        )


@router.post("/{freelancer_id}/edit")
async def update_freelancer(
    freelancer_id: int,
    name: str = Form(...),
    phone_number: str = Form(...),
    email: str = Form(...),
    address: str = Form(None),
    role: str = Form(...),
    per_day_charge: float = Form(0.0),
    per_project_charge: float = Form(0.0),
    bank_name: str = Form(None),
    account_number: str = Form(None),
    ifsc_code: str = Form(None),
    upi_id: str = Form(None),
    pan_number: str = Form(None),
    aadhar_number: str = Form(None),
    status: str = Form("Active"),
    remarks: str = Form(None),
    aadhar_card: UploadFile = File(None),
    resume: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    """Update freelancer profile details and optionally documents."""
    try:
        freelancer = db.query(Freelancer).filter(Freelancer.id == freelancer_id).first()
        if not freelancer:
            raise HTTPException(status_code=404, detail="Freelancer not found")
            
        # Save documents if newly uploaded
        aadhar_card_filename = save_uploaded_file(aadhar_card)
        if aadhar_card_filename:
            # Delete old file
            delete_file(freelancer.aadhar_card_path)
            freelancer.aadhar_card_path = aadhar_card_filename
            
        resume_filename = save_uploaded_file(resume)
        if resume_filename:
            # Delete old file
            delete_file(freelancer.resume_path)
            freelancer.resume_path = resume_filename
            
        # Update details
        freelancer.name = name
        freelancer.phone_number = phone_number
        freelancer.email = email
        freelancer.address = address
        freelancer.role = role
        freelancer.per_day_charge = per_day_charge
        freelancer.per_project_charge = per_project_charge
        freelancer.bank_name = bank_name
        freelancer.account_number = account_number
        freelancer.ifsc_code = ifsc_code
        freelancer.upi_id = upi_id
        freelancer.pan_number = pan_number
        freelancer.aadhar_number = aadhar_number
        freelancer.status = status
        freelancer.remarks = remarks
        freelancer.updated_at = datetime.utcnow()
        
        db.commit()
        
        return RedirectResponse(url=f"/freelancers/{freelancer.id}", status_code=303)
        
    except Exception as e:
        db.rollback()
        print(f"Error updating freelancer: {str(e)}")
        raise


@router.post("/{freelancer_id}/delete")
async def delete_freelancer(
    freelancer_id: int,
    db: Session = Depends(get_db)
):
    """Delete freelancer profile and cleanup physical documents."""
    try:
        freelancer = db.query(Freelancer).filter(Freelancer.id == freelancer_id).first()
        if not freelancer:
            raise HTTPException(status_code=404, detail="Freelancer not found")
            
        # Clean up files
        delete_file(freelancer.aadhar_card_path)
        delete_file(freelancer.resume_path)
        
        # SQLAlchemy handles cascade delete for payments relationship automatically
        db.delete(freelancer)
        db.commit()
        
        return RedirectResponse(url="/freelancers/", status_code=303)
        
    except Exception as e:
        db.rollback()
        print(f"Error deleting freelancer: {str(e)}")
        raise


@router.get("/{freelancer_id}/download/{file_type}")
async def download_document(
    freelancer_id: int,
    file_type: str,
    db: Session = Depends(get_db)
):
    """Securely download resume or Aadhar card file."""
    try:
        freelancer = db.query(Freelancer).filter(Freelancer.id == freelancer_id).first()
        if not freelancer:
            raise HTTPException(status_code=404, detail="Freelancer not found")
            
        filename = None
        display_name = ""
        
        if file_type == "aadhar":
            filename = freelancer.aadhar_card_path
            display_name = f"Aadhar_Card_{freelancer.name.replace(' ', '_')}"
        elif file_type == "resume":
            filename = freelancer.resume_path
            display_name = f"Resume_{freelancer.name.replace(' ', '_')}"
        else:
            raise HTTPException(status_code=400, detail="Invalid file type. Select 'aadhar' or 'resume'.")
            
        if not filename:
            raise HTTPException(status_code=404, detail="Requested file was not uploaded.")
            
        filepath = os.path.join(UPLOAD_DIR, filename)
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="Physical file not found on the server.")
            
        # Extract extension
        ext = filename.split('.')[-1]
        
        return FileResponse(
            path=filepath,
            filename=f"{display_name}.{ext}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error downloading file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================================
# WORK LOGS & PAYMENTS ASSIGNMENT ROUTES
# ==========================================================

@router.get("/{freelancer_id}/work/add", response_class=HTMLResponse)
async def add_work_form(
    request: Request,
    freelancer_id: int,
    db: Session = Depends(get_db)
):
    """Display add assignment/work log form."""
    try:
        freelancer = db.query(Freelancer).filter(Freelancer.id == freelancer_id).first()
        if not freelancer:
            return templates.TemplateResponse(
                "error.html",
                {"request": request, "error": "Freelancer not found"},
                status_code=404
            )
            
        roles = ["Photographer", "Videographer", "Editor", "Cinematographer", "Drone Operator", "Designer", "Other"]
        context = {
            "request": request,
            "page_title": f"Log Work Assignment: {freelancer.name}",
            "freelancer": freelancer,
            "roles": roles,
            "all_project_names": get_all_project_names(db),
            "is_edit": False
        }
        
        return templates.TemplateResponse("freelancers/work_form.html", context)
        
    except Exception as e:
        print(f"Error loading work log form: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": str(e)},
            status_code=500
        )


@router.post("/{freelancer_id}/work/add")
async def create_work_log(
    request: Request,
    freelancer_id: int,
    db: Session = Depends(get_db)
):
    """Create a new work assignment and payment log."""
    try:
        freelancer = db.query(Freelancer).filter(Freelancer.id == freelancer_id).first()
        if not freelancer:
            raise HTTPException(status_code=404, detail="Freelancer not found")
            
        form_data = await request.form()
        project_name = form_data.get("project_name")
        role_assigned = form_data.get("role_assigned")
        amount_charged = float(form_data.get("amount_charged", 0.0))
        num_days = int(form_data.get("num_days", 1))
        total_amount = float(form_data.get("total_amount", 0.0))
        payment_status = form_data.get("payment_status", "Pending")
        payment_date = form_data.get("payment_date")
        payment_mode = form_data.get("payment_mode")
        remarks = form_data.get("remarks")
        
        work_dates = form_data.getlist("work_date[]")
        if not work_dates and form_data.get("work_date"):
            work_dates = [form_data.get("work_date")]
            
        first_date_str = work_dates[0] if work_dates else str(datetime.utcnow().date())
        w_date = datetime.strptime(first_date_str, "%Y-%m-%d").date()
        
        # Parse payment date
        p_date = None
        if payment_date and payment_status == "Paid":
            p_date = datetime.strptime(payment_date, "%Y-%m-%d").date()
            
        # Optional: Save multiple dates into remarks if more than one
        if len(work_dates) > 1:
            date_str = ", ".join(work_dates)
            remarks = f"{remarks}\nWork Dates: {date_str}" if remarks else f"Work Dates: {date_str}"
            
        record = FreelancerWork(
            freelancer_id=freelancer.id,
            project_name=project_name,
            work_date=w_date,
            role_assigned=role_assigned,
            num_days=num_days,
            amount_charged=amount_charged,
            total_amount=total_amount,
            payment_status=payment_status,
            payment_date=p_date,
            payment_mode=payment_mode if payment_status == "Paid" else None,
            remarks=remarks
        )
        
        db.add(record)
        db.commit()
        
        return RedirectResponse(url=f"/freelancers/{freelancer.id}", status_code=303)
        
    except Exception as e:
        db.rollback()
        print(f"Error creating work assignment log: {str(e)}")
        raise


@router.get("/{freelancer_id}/work/{work_id}/edit", response_class=HTMLResponse)
async def edit_work_form(
    request: Request,
    freelancer_id: int,
    work_id: int,
    db: Session = Depends(get_db)
):
    """Display edit assignment/work log form."""
    try:
        freelancer = db.query(Freelancer).filter(Freelancer.id == freelancer_id).first()
        work = db.query(FreelancerWork).filter(FreelancerWork.id == work_id).first()
        
        if not freelancer or not work:
            return templates.TemplateResponse(
                "error.html",
                {"request": request, "error": "Record not found"},
                status_code=404
            )
            
        roles = ["Photographer", "Videographer", "Editor", "Cinematographer", "Drone Operator", "Designer", "Other"]
        context = {
            "request": request,
            "page_title": f"Edit Assignment: {work.project_name}",
            "freelancer": freelancer,
            "work": work,
            "roles": roles,
            "all_project_names": get_all_project_names(db),
            "is_edit": True
        }
        
        return templates.TemplateResponse("freelancers/work_form.html", context)
        
    except Exception as e:
        print(f"Error loading work edit form: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": str(e)},
            status_code=500
        )


@router.post("/{freelancer_id}/work/{work_id}/edit")
async def update_work_log(
    request: Request,
    freelancer_id: int,
    work_id: int,
    db: Session = Depends(get_db)
):
    """Update work assignment and payment log details."""
    try:
        work = db.query(FreelancerWork).filter(FreelancerWork.id == work_id).first()
        if not work:
            raise HTTPException(status_code=404, detail="Work record not found")
            
        form_data = await request.form()
        project_name = form_data.get("project_name")
        role_assigned = form_data.get("role_assigned")
        amount_charged = float(form_data.get("amount_charged", 0.0))
        num_days = int(form_data.get("num_days", 1))
        total_amount = float(form_data.get("total_amount", 0.0))
        payment_status = form_data.get("payment_status", "Pending")
        payment_date = form_data.get("payment_date")
        payment_mode = form_data.get("payment_mode")
        remarks = form_data.get("remarks")
        
        work_dates = form_data.getlist("work_date[]")
        if not work_dates and form_data.get("work_date"):
            work_dates = [form_data.get("work_date")]
            
        first_date_str = work_dates[0] if work_dates else str(datetime.utcnow().date())
        w_date = datetime.strptime(first_date_str, "%Y-%m-%d").date()
        
        p_date = None
        if payment_date and payment_status == "Paid":
            p_date = datetime.strptime(payment_date, "%Y-%m-%d").date()
            
        # Optional: Save multiple dates into remarks if more than one
        if len(work_dates) > 1:
            date_str = ", ".join(work_dates)
            remarks = f"{remarks}\nWork Dates: {date_str}" if remarks else f"Work Dates: {date_str}"
            
        work.project_name = project_name
        work.work_date = w_date
        work.role_assigned = role_assigned
        work.num_days = num_days
        work.amount_charged = amount_charged
        work.total_amount = total_amount
        work.payment_status = payment_status
        work.payment_date = p_date
        work.payment_mode = payment_mode if payment_status == "Paid" else None
        work.remarks = remarks
        work.updated_at = datetime.utcnow()
        
        db.commit()
        
        return RedirectResponse(url=f"/freelancers/{freelancer_id}", status_code=303)
        
    except Exception as e:
        db.rollback()
        print(f"Error updating work log assignment: {str(e)}")
        raise


@router.post("/{freelancer_id}/work/{work_id}/delete")
async def delete_work_log(
    freelancer_id: int,
    work_id: int,
    db: Session = Depends(get_db)
):
    """Delete a work assignment/payment log."""
    try:
        work = db.query(FreelancerWork).filter(FreelancerWork.id == work_id).first()
        if not work:
            raise HTTPException(status_code=404, detail="Work record not found")
            
        db.delete(work)
        db.commit()
        
        return RedirectResponse(url=f"/freelancers/{freelancer_id}", status_code=303)
        
    except Exception as e:
        db.rollback()
        print(f"Error deleting work log record: {str(e)}")
        raise
