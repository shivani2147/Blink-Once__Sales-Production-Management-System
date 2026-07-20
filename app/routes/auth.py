from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str = None):
    # Check if already logged in
    if request.session.get("user"):
        return RedirectResponse(url="/dashboard", status_code=303)
    return templates.TemplateResponse("auth/login.html", {"request": request, "error": error})

@router.post("/login")
async def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    # Simple hardcoded authentication for now
    if username == "admin" and password == "admin123":
        request.session["user"] = "admin"
        return RedirectResponse(url="/dashboard", status_code=303)
    
    return templates.TemplateResponse("auth/login.html", {
        "request": request, 
        "error": "Invalid username or password"
    })

@router.get("/logout")
async def logout(request: Request):
    request.session.pop("user", None)
    return RedirectResponse(url="/login", status_code=303)
