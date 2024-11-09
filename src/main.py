from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.routes.upload import upload_router
from src.routes.process_image import process_image_router

#  Create FastAPI app
app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Including routes
app.include_router(upload_router)
app.include_router(process_image_router)
