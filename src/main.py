from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.api.verify import verify_router
from src.routes.upload import upload_router

# Создаем приложение FastAPI
app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Подключаем роуты
app.include_router(verify_router)
app.include_router(upload_router)
