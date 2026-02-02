from fastapi import APIRouter, Response, HTTPException, Request
from app.services import cognito_service as cs
from app.schemas.auth_schemas import *
from app.core.config import settings
import requests

router = APIRouter(prefix="/auth", tags=["Authentication"])

# ------------------ SIGNUP / LOGIN ------------------

@router.post("/signup")
def signup(data: SignUpSchema):
    return cs.signup(data.email, data.password)


@router.post("/confirm-signup")
def confirm_signup(data: ConfirmSchema):
    return cs.confirm_signup(data.email, data.otp)


@router.post("/login")
def login(data: LoginSchema, response: Response):
    tokens = cs.login(data.email, data.password)

    response.set_cookie(
        "access_token",
        tokens["access_token"],
        httponly=True,
        samesite="lax",
        secure=False  # True in production with HTTPS
    )

    response.set_cookie(
        "refresh_token",
        tokens["refresh_token"],
        httponly=True,
        samesite="lax",
        secure=False
    )

    return {"message": "Login successful"}


# ------------------ GOOGLE LOGIN ------------------

@router.get("/google-login")
def google_login():
    return {
        "login_url": (
            f"{settings.COGNITO_DOMAIN}/login?"
            f"client_id={settings.COGNITO_CLIENT_ID}"
            f"&response_type=code"
            f"&scope=email+openid+profile"
            f"&redirect_uri={settings.CALLBACK_URL}"
            f"&identity_provider=Google"
        )
    }


@router.get("/callback")
def callback(code: str, response: Response):
    token_url = f"{settings.COGNITO_DOMAIN}/oauth2/token"

    data = {
        "grant_type": "authorization_code",
        "client_id": settings.COGNITO_CLIENT_ID,
        "code": code,
        "redirect_uri": settings.CALLBACK_URL,
    }

    r = requests.post(token_url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})

    if r.status_code != 200:
        raise HTTPException(400, r.text)

    tokens = r.json()

    response.set_cookie("access_token", tokens["access_token"], httponly=True)
    response.set_cookie("refresh_token", tokens["refresh_token"], httponly=True)

    return {"message": "Google login successful"}


# ------------------ LOGOUT ------------------

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out successfully"}


# ------------------ PASSWORD FLOWS ------------------

@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordSchema):
    return cs.forgot_password(data.email)


@router.post("/reset-password")
def reset_password(data: ResetPasswordSchema):
    return cs.reset_password(data.email, data.otp, data.new_password)


# ------------------ TOKEN REFRESH ------------------

@router.post("/refresh")
def refresh_token(request: Request, response: Response):
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    token_url = f"{settings.COGNITO_DOMAIN}/oauth2/token"

    data = {
        "grant_type": "refresh_token",
        "client_id": settings.COGNITO_CLIENT_ID,
        "refresh_token": refresh_token,
    }

    r = requests.post(token_url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})

    if r.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    tokens = r.json()

    response.set_cookie(
        "access_token",
        tokens["access_token"],
        httponly=True,
        samesite="lax",
        secure=False
    )

    return {"message": "Token refreshed"}
