"""
Configuration module for ProductionFlow CRM
Contains database connection settings, app settings, and environment variables.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Base Directory
BASE_DIR = Path(__file__).resolve().parent.parent

# SQL Server Configuration (loaded from .env)
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# FastAPI Settings
APP_TITLE = "ProductionFlow CRM"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Professional Sales & Production Management System for Creative Production Companies"

# File Upload Settings
UPLOAD_DIR = os.path.join(BASE_DIR, "app", "uploads")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "xls", "xlsx", "jpg", "jpeg", "png"}

# Session Settings
SECRET_KEY = "your-secret-key-change-in-production"
SESSION_TIMEOUT = 3600  # 1 hour in seconds

# Pagination Settings
ITEMS_PER_PAGE = 20

# App Settings
DEBUG = True
RELOAD = True

# Email Settings (for future use)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "your-email@gmail.com"
SENDER_PASSWORD = "your-app-password"

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)
