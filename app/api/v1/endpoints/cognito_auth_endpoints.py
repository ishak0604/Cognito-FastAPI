from fastapi import APIRouter, Response, HTTPException
from fastapi.responses import RedirectResponse
from app.services import cognito_service as cs
from app.schemas.auth_schemas import (
    SignUpSchema, ConfirmSchema, LoginSchema,
    ForgotPasswordSchema, ResetPasswordSchema
)
from app.core.config import settings
import requests

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ------------------ SIGNUP ------------------
@router.post("/signup")
def signup(data: SignUpSchema):
    return cs.signup(data.email, data.password)


@router.post("/confirm-signup")
def confirm_signup(data: ConfirmSchema):
    return cs.confirm_signup(data.email, data.otp)


# ------------------ LOGIN (API) ------------------
@router.post("/login")
def login(data: LoginSchema, response: Response):
    tokens = cs.login(data.email, data.password)

    response.set_cookie(
        key="access_token",
        value=tokens["access_token"],
        httponly=True,
        secure=False,
        samesite="lax"
    )

    response.set_cookie(
        key="refresh_token",
        value=tokens["refresh_token"],
        httponly=True,
        secure=False,
        samesite="lax"
    )

    return {"message": "Login successful"}



# ------------------ GOOGLE LOGIN (Hosted UI) ------------------
@router.get("/google-login")
def google_login():
    login_url = (
        f"{settings.COGNITO_DOMAIN}/login?"
        f"client_id={settings.COGNITO_CLIENT_ID}"
        f"&response_type=code"
        f"&scope=email+openid+profile"
        f"&redirect_uri={settings.CALLBACK_URL}"
        f"&identity_provider=Google"
    )
    return {"login_url": login_url}



# ------------------ CALLBACK (OAuth Code → Tokens) ------------------
@router.get("/callback")
def callback(code: str, response: Response):
    token_url = f"{settings.COGNITO_DOMAIN}/oauth2/token"

    data = {
        "grant_type": "authorization_code",
        "client_id": settings.COGNITO_CLIENT_ID,
        "code": code,
        "redirect_uri": settings.CALLBACK_URL,
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r = requests.post(token_url, data=data, headers=headers)

    if r.status_code != 200:
        raise HTTPException(400, "Token exchange failed")

    tokens = r.json()

    response.set_cookie("access_token", tokens["access_token"], httponly=True)
    response.set_cookie("refresh_token", tokens["refresh_token"], httponly=True)

    return {"message": "Login via Google successful"}


# ------------------ LOGOUT ------------------
@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}



# ------------------ PASSWORD FLOWS ------------------
@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordSchema):
    return cs.forgot_password(data.email)


@router.post("/reset-password")
def reset_password(data: ResetPasswordSchema):
    return cs.reset_password(data.email, data.otp, data.new_password)
