"""
SQLAlchemy ORM models for ProductionFlow CRM.
Defines database tables for Pre-Production, On-Production, Post-Production, and Checklist modules.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, Date, NVARCHAR, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base



class PreProduction(Base):
    """Pre-Production module model for managing pre-production activities."""
    __tablename__ = "pre_production"
    
    id = Column(Integer, primary_key=True, index=True)
    couple_name = Column(String(255), nullable=False, index=True)
    client_email = Column(String(255), nullable=False)
    event_type = Column(String(255), nullable=False)
    event_date = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=False)
    
    year = Column(Integer, nullable=True)
    month = Column(String(20), nullable=True)
    
    # Status tracking
    referral_program = Column(Boolean, default=False)
    advance_retainer_received = Column(Boolean, default=False)
    welcome_call = Column(Boolean, default=False)
    team_booking = Column(Boolean, default=False)
    story_designing_call = Column(Boolean, default=False)
    heartfelt_email_cra = Column(Boolean, default=False)
    terms_confirmation_cra = Column(Boolean, default=False)
    invoicing_cra = Column(Boolean, default=False)
    sending_jd_to_team = Column(Boolean, default=False)
    music_choice_link_cra = Column(Boolean, default=False)
    invitation_video = Column(Boolean, default=False)
    whatsapp_group = Column(Boolean, default=False)
    
    # Additional fields
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), nullable=True)
    
    def get_completion_percentage(self):
        """Calculate completion percentage of pre-production tasks."""
        fields = [
            self.advance_retainer_received, self.welcome_call, self.team_booking,
            self.story_designing_call, self.heartfelt_email_cra, self.terms_confirmation_cra,
            self.invoicing_cra, self.sending_jd_to_team, self.music_choice_link_cra,
            self.invitation_video, self.whatsapp_group
        ]
        completed = sum(1 for field in fields if field)
        return int((completed / len(fields)) * 100) if fields else 0


class OnProduction(Base):
    """On-Production module model for managing on-production day activities."""
    __tablename__ = "on_production"
    
    id = Column(Integer, primary_key=True, index=True)
    couple_name = Column(String(255), nullable=False, index=True)
    event_date = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=False)
    
    year = Column(Integer, nullable=True)
    month = Column(String(20), nullable=True)
    
    # Status tracking
    client_review = Column(Boolean, default=False)
    payment_received = Column(Boolean, default=False)
    bts_shoot = Column(Boolean, default=False)
    hospitality_gesture = Column(Boolean, default=False)
    story_designing_sheet_refer = Column(Boolean, default=False)
    checklist_shared_with_team = Column(Boolean, default=False)
    
    # Team coordination
    assigned_team_members = Column(Text, nullable=True)  # Comma-separated names
    team_feedback = Column(Text, nullable=True)
    
    # Additional fields
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), nullable=True)
    
    def get_completion_percentage(self):
        """Calculate completion percentage of on-production tasks."""
        fields = [
            self.client_review, self.payment_received, self.bts_shoot,
            self.hospitality_gesture, self.story_designing_sheet_refer,
            self.checklist_shared_with_team
        ]
        completed = sum(1 for field in fields if field)
        return int((completed / len(fields)) * 100) if fields else 0


class PostProduction(Base):
    """Post-Production module model for managing post-production deliverables."""
    __tablename__ = "post_production"
    
    id = Column(Integer, primary_key=True, index=True)
    couple_name = Column(String(255), nullable=False, index=True)
    event_date = Column(String(255), nullable=False)
    deadline = Column(Date, nullable=False)
    event_name = Column(String(255), nullable=True)
    
    year = Column(Integer, nullable=True)
    month = Column(String(20), nullable=True)
    
    # Delivery tracking
    data_copy = Column(Boolean, default=False)
    best_couple_edits_3_days = Column(Boolean, default=False)
    all_raw_images = Column(Boolean, default=False)
    save_the_date = Column(Boolean, default=False)
    invite = Column(Boolean, default=False)
    countdown = Column(Boolean, default=False)
    celebrity_ai_reel = Column(Boolean, default=False)
    one_teaser = Column(Boolean, default=False)
    one_film = Column(Boolean, default=False)
    one_reel = Column(Boolean, default=False)
    full_length_film = Column(Boolean, default=False)
    edited_images_selection = Column(Boolean, default=False)
    edited_images_delivered = Column(Boolean, default=False)
    poster = Column(Boolean, default=False)
    albums_picture_selection = Column(Boolean, default=False)
    photobook_delivered = Column(Boolean, default=False)
    digital_portfolio_album = Column(Boolean, default=False)
    payment_recovery = Column(Boolean, default=False)
    
    # Closure
    closure_date = Column(Date, nullable=True)
    remarks = Column(Text, nullable=True)
    
    # Additional fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), nullable=True)
    
    def get_completion_percentage(self):
        """Calculate completion percentage of post-production tasks."""
        fields = [
            self.data_copy, self.best_couple_edits_3_days, self.all_raw_images,
            self.save_the_date, self.invite, self.countdown, self.celebrity_ai_reel,
            self.one_teaser, self.one_film, self.one_reel, self.full_length_film,
            self.edited_images_selection, self.edited_images_delivered, self.poster,
            self.albums_picture_selection, self.photobook_delivered,
            self.digital_portfolio_album, self.payment_recovery
        ]
        completed = sum(1 for field in fields if field)
        return int((completed / len(fields)) * 100) if fields else 0
    
    def is_overdue(self):
        """Check if deadline has passed."""
        return datetime.now().date() > self.deadline if self.deadline else False


class Checklist(Base):
    """Checklist module model for equipment and role-based checklists."""
    __tablename__ = "checklists"
    
    id = Column(Integer, primary_key=True, index=True)
    couple_name = Column(String(255), nullable=False, index=True)
    event_date = Column(Date, nullable=False)
    
    # Equipment checklist
    equipments_ready = Column(Boolean, default=False)
    equipment_notes = Column(Text, nullable=True)
    
    # Role-based responsibilities
    traditional_videographer = Column(Boolean, default=False)
    videographer_notes = Column(Text, nullable=True)
    
    traditional_photographer = Column(Boolean, default=False)
    photographer_notes = Column(Text, nullable=True)
    
    candid_photographer = Column(Boolean, default=False)
    candid_notes = Column(Text, nullable=True)
    
    cinematographer = Column(Boolean, default=False)
    cinematographer_notes = Column(Text, nullable=True)
    
    drone_shooter = Column(Boolean, default=False)
    drone_notes = Column(Text, nullable=True)
    
    pre_wedding_shoot = Column(Boolean, default=False)
    pre_wedding_notes = Column(Text, nullable=True)
    
    # Assignment details
    assigned_team = Column(Text, nullable=True)
    checklist_status = Column(String(50), default="pending")  # pending, in-progress, completed
    
    # Additional fields
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), nullable=True)
    
    def get_completion_percentage(self):
        """Calculate completion percentage of checklist tasks."""
        fields = [
            self.equipments_ready, self.traditional_videographer,
            self.traditional_photographer, self.candid_photographer,
            self.cinematographer, self.drone_shooter, self.pre_wedding_shoot
        ]
        completed = sum(1 for field in fields if field)
        return int((completed / len(fields)) * 100) if fields else 0

    def get_info_completion_percentage(self):
        """Calculate completion percentage based on checklist information fields."""
        fields = [
            self.equipment_notes, self.videographer_notes, self.photographer_notes,
            self.candid_notes, self.cinematographer_notes, self.drone_notes,
            self.pre_wedding_notes, self.assigned_team
        ]
        completed = sum(1 for field in fields if field and str(field).strip())
        return int((completed / len(fields)) * 100) if fields else 0


# YEARLY FINANCIAL DATA MODELS

class MonthlyFinancialReport(Base):
    """Monthly Financial Report for tracking revenue, expenses, and profit."""
    __tablename__ = "monthly_financial_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    month = Column(String(50), nullable=False, index=True)  # Month name selected
    year = Column(Integer, nullable=False, index=True)  # Year selected
    client_name = Column(String(255), nullable=False, index=True)
    project_name = Column(String(255), nullable=True)
    event_type = Column(String(255), nullable=False)
    event_date = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    requirements = Column(Text, nullable=True)
    
    # Financial fields
    total_amount = Column(Float, nullable=False, default=0.0)
    paid_amount = Column(Float, nullable=False, default=0.0)
    pending_amount = Column(Float, nullable=False, default=0.0)
    freelancer_amount = Column(Float, nullable=False, default=0.0)
    expenses = Column(Float, nullable=False, default=0.0)
    profit = Column(Float, nullable=False, default=0.0)
    
    # Status tracking
    payment_status = Column(String(50), nullable=False)  # Online, Cash
    work_status = Column(String(50), nullable=False, default="Pending")  # Pending, Done
    
    # Additional fields
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), nullable=True)
    
    def calculate_pending(self):
        """Calculate pending amount."""
        self.pending_amount = self.total_amount - self.paid_amount
        return self.pending_amount
    
    def calculate_profit(self):
        """Calculate profit."""
        # Profit should reflect actual earnings: paid amount minus costs
        self.profit = self.paid_amount - self.freelancer_amount - self.expenses
        return self.profit


class ThreeMonthsClientFollowup(Base):
    """Client Follow-up for lead tracking and conversion."""
    __tablename__ = "three_months_client_followup"
    
    id = Column(Integer, primary_key=True, index=True)
    # Updated to DateTime to accept datetime values during inserts
    date = Column(Date, nullable=False, default=datetime.now().date(), index=True)
    year = Column(Integer, nullable=False, default=datetime.now().year, index=True)
    month = Column(String(50), nullable=False, default=datetime.now().strftime('%B'), index=True)
    client_name = Column(String(255), nullable=False, index=True)
    event_type = Column(String(255), nullable=False)
    event_date = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    phone_number = Column(String(20), nullable=False)
    
    # Financial tracking
    client_budget = Column(Float, nullable=False, default=0.0)
    total_amount = Column(Float, nullable=False, default=0.0)
    
    # Lead tracking
    platform = Column(String(100), nullable=False)  # JD, Meta Ads, Word of Mouth
    negotiation = Column(Boolean, default=False)
    confirmation = Column(Float, nullable=False, default=0.0)
    
    # Status tracking
    status = Column(String(50), nullable=False)  # Done, Pending, Rejected, Not replied, etc.
    
    # Additional fields
    comment = Column(Text, nullable=True)
    requirements = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), nullable=True)


class InvestmentToGrowCompany(Base):
    """Investment To Grow Company for tracking investments and expenses."""
    __tablename__ = "investment_to_grow_company"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    service = Column(String(255), nullable=False)  # Type of investment
    total_amount = Column(Float, nullable=False, default=0.0)
    paid_amount = Column(Float, nullable=False, default=0.0)
    pending_amount = Column(Float, nullable=False, default=0.0)
    payment_mode = Column(String(50), nullable=True)  # Cash or Online
    payment_status = Column(String(50), nullable=True, default="Done")  # Done or Pending
    
    # Additional fields
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), nullable=True)


class ClientsEditing(Base):
    """Clients Editing for tracking editing workload and revenue."""
    __tablename__ = "clients_editing"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    client_name = Column(String(255), nullable=False, index=True)
    editing_type = Column(String(255), nullable=False)
    total_amount = Column(Float, nullable=False, default=0.0)
    paid_amount = Column(Float, nullable=False, default=0.0)
    pending_amount = Column(Float, nullable=False, default=0.0)
    
    # Status tracking
    payment_status = Column(String(50), nullable=False)  # Online, Cash
    work_status = Column(String(50), nullable=False, default="Pending")  # Pending, Done
    
    # Additional fields
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), nullable=True)


class CameraRent(Base):
    """Camera Rent for tracking rental income and equipment usage."""
    __tablename__ = "camera_rent"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    client_name = Column(String(255), nullable=False, index=True)
    description_of_goods = Column(String(255), nullable=False)
    days = Column(Integer, nullable=False, default=1)
    phone_number = Column(String(20), nullable=False)
    aadhar_card_no = Column(String(20), nullable=True)
    total_amount = Column(Numeric(12, 2), nullable=False, default=0.0)
    paid_amount = Column(Numeric(12, 2), nullable=False, default=0.0)
    pending_amount = Column(Numeric(12, 2), nullable=False, default=0.0)
    
    # Status tracking
    payment_status = Column(String(50), nullable=False)  # Online, Cash
    work_status = Column(String(50), nullable=False, default="Pending")  # Pending, Done
    
    # Additional fields
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), nullable=True)


class UpcomingClientsShoot(Base):
    """Upcoming Clients Shoot for shoot scheduling and pipeline management."""
    __tablename__ = "upcoming_shoots"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    client_name = Column(String(255), nullable=False, index=True)
    event_type = Column(String(255), nullable=False)
    event_date = Column(String(255), nullable=False, index=True)
    phone_number = Column(String(20), nullable=False)
    total_amount = Column(Float, nullable=False, default=0.0)
    
    # Lead tracking
    negotiation = Column(Float, nullable=False, default=0.0)
    confirmation = Column(String(255), nullable=True)
    
    # Status tracking
    status = Column(String(50), nullable=False)  # Pending, Done, Rejected
    
    # Additional fields
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), nullable=True)


class Freelancer(Base):
    """Freelancer profiles model."""
    __tablename__ = "freelancers"
    
    id = Column(Integer, primary_key=True, index=True)
    freelancer_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False, index=True)
    phone_number = Column(String(20), nullable=False)
    email = Column(String(255), nullable=False)
    address = Column(Text, nullable=True)
    role = Column(String(100), nullable=False, index=True)
    per_day_charge = Column(Float, default=0.0)
    per_project_charge = Column(Float, default=0.0)
    bank_name = Column(String(255), nullable=True)
    account_number = Column(String(100), nullable=True)
    ifsc_code = Column(String(50), nullable=True)
    upi_id = Column(String(255), nullable=True)
    pan_number = Column(String(50), nullable=True)
    aadhar_number = Column(String(50), nullable=True)
    status = Column(String(50), nullable=False, default="Active")
    remarks = Column(Text, nullable=True)
    aadhar_card_path = Column(String(500), nullable=True)
    resume_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    payments = relationship("FreelancerWork", back_populates="freelancer", cascade="all, delete-orphan")


class FreelancerWork(Base):
    """Freelancer project assignments and payment tracking."""
    __tablename__ = "freelancer_works"
    
    id = Column(Integer, primary_key=True, index=True)
    freelancer_id = Column(Integer, ForeignKey('freelancers.id', ondelete='CASCADE'), nullable=False)
    project_name = Column(String(255), nullable=False)
    work_date = Column(Date, nullable=False)
    work_dates = Column(String(500), nullable=True)
    role_assigned = Column(String(100), nullable=False)
    num_days = Column(Integer, default=1, nullable=False)
    amount_charged = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)
    paid_amount = Column(Float, default=0.0)
    pending_amount = Column(Float, default=0.0)
    payment_status = Column(String(50), default="Pending")  # Pending / Paid
    payment_date = Column(Date, nullable=True)
    payment_mode = Column(String(100), nullable=True)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    freelancer = relationship("Freelancer", back_populates="payments")

    @property
    def work_dates_display(self):
        if self.work_dates:
            try:
                parts = [p.strip() for p in self.work_dates.split(',') if p.strip()]
                formatted = [datetime.strptime(p, '%Y-%m-%d').strftime('%d-%m-%Y') for p in parts]
                return ', '.join(formatted)
            except Exception:
                return self.work_dates
        if self.work_date:
            return self.work_date.strftime('%d-%m-%Y')
        return '-'

