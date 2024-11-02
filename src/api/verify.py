import httpx
from fastapi import APIRouter, Form, HTTPException

verify_router = APIRouter()

RECAPTCHA_SECRET_KEY = "secret"

@verify_router.post("/verify-captcha")
async def verify_captcha(captcha_response: str = Form(...)):
    """
    Проверяет Google reCAPTCHA ответ пользователя.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data={
                "secret": RECAPTCHA_SECRET_KEY,
                "response": captcha_response
            }
        )
        result = response.json()

    if not result.get("success"):
        raise HTTPException(status_code=400, detail="Ошибка верификации reCAPTCHA")

    return {"message": "reCAPTCHA верифицирована успешно"}
