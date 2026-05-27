# Quick Start Guide for ProductionFlow CRM

## ⚡ Quick Start (5 minutes)

### 1. Setup Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Verify SQL Server Connection
- Server: `BO-LAPTOP\SQLEXPRESS`
- Database: `BlinkOnce__ProductionManagementSystem`
- Ensure database exists

### 4. Run Application
```bash
python main.py
```

### 5. Access Dashboard
Open browser: `http://localhost:8000/dashboard`

---

## 📋 First Time Setup Checklist

- [ ] Python 3.12+ installed
- [ ] Virtual environment created
- [ ] Dependencies installed via pip
- [ ] SQL Server running and accessible
- [ ] ODBC Driver 17 installed
- [ ] Database created in SQL Server
- [ ] Application started without errors
- [ ] Dashboard accessible in browser

---

## 🚀 Features to Try

1. **Dashboard** - Overview of all modules
2. **Pre-Production** - Add/edit/view pre-production records
3. **On-Production** - Manage production day activities
4. **Post-Production** - Track deliverables and deadlines
5. **Checklist** - Manage equipment and team roles

---

## 📚 Documentation

- Full README: See README.md
- API Docs: http://localhost:8000/api/docs
- Source Code: Check app/ directory

---

## ❓ Need Help?

- Check README.md Troubleshooting section
- Verify SQL Server connection
- Ensure all dependencies installed
- Check ODBC driver installation

---

## 🎯 Next Steps

1. Configure database connection (if different from default)
2. Create first pre-production record
3. Explore all modules
4. Customize branding/settings as needed

Happy Production Management! 🎬📸
