from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

import os
from fastapi import APIRouter
from dotenv import load_dotenv

# Loading data from .env
load_dotenv()

# Retreiving secret key from env
RECAPTCHA_PUBLIC_KEY = os.getenv("RECAPTCHA_PUBLIC_KEY")

# Create the router
upload_router = APIRouter()

# Initialize Jinja2Templates
templates = Jinja2Templates(directory="src/templates")

@upload_router.get("/upload-image", response_class=HTMLResponse)
async def upload_page(request: Request):
    # Render the page with the image upload form
    return templates.TemplateResponse("upload.html", {"request": request, "recaptcha_public_key": RECAPTCHA_PUBLIC_KEY,})
