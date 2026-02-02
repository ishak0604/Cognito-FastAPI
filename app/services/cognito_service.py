import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException, status
from app.core.config import settings
from app.database import SessionLocal
from app.models.user import User

client = boto3.client("cognito-idp", region_name=settings.AWS_REGION)


# ---------------- SIGNUP ----------------
def signup(email: str, password: str):
    try:
        client.sign_up(
            ClientId=settings.COGNITO_CLIENT_ID,
            Username=email,
            Password=password,
            UserAttributes=[{"Name": "email", "Value": email}],
        )
        return {"message": "OTP sent to email"}

    except ClientError as e:
        raise HTTPException(400, e.response["Error"]["Message"])


# ---------------- CONFIRM SIGNUP ----------------
def confirm_signup(email: str, otp: str):
    db = SessionLocal()
    try:
        client.confirm_sign_up(
            ClientId=settings.COGNITO_CLIENT_ID,
            Username=email,
            ConfirmationCode=otp,
        )

        user = client.admin_get_user(
            UserPoolId=settings.COGNITO_USER_POOL_ID,
            Username=email,
        )

        sub = next(attr["Value"] for attr in user["UserAttributes"] if attr["Name"] == "sub")

        if not db.query(User).filter_by(id=sub).first():
            db.add(User(id=sub, email=email))
            db.commit()

        return {"message": "Account verified"}

    except ClientError as e:
        db.rollback()
        raise HTTPException(400, e.response["Error"]["Message"])
    finally:
        db.close()


# ---------------- LOGIN ----------------
def login(email: str, password: str):
    try:
        res = client.initiate_auth(
            ClientId=settings.COGNITO_CLIENT_ID,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": email,
                "PASSWORD": password,
            },
        )

        tokens = res["AuthenticationResult"]

        return {
            "access_token": tokens["AccessToken"],
            "refresh_token": tokens.get("RefreshToken"),
            "id_token": tokens["IdToken"],
        }

    except ClientError as e:
        msg = e.response["Error"]["Message"]

        if "User is not confirmed" in msg:
            raise HTTPException(403, "Please confirm your email before login")

        raise HTTPException(401, msg)


# ---------------- FORGOT PASSWORD ----------------
def forgot_password(email: str):
    try:
        client.forgot_password(ClientId=settings.COGNITO_CLIENT_ID, Username=email)
        return {"message": "Reset code sent"}
    except ClientError as e:
        raise HTTPException(400, e.response["Error"]["Message"])


# ---------------- RESET PASSWORD ----------------
def reset_password(email: str, code: str, new_password: str):
    try:
        client.confirm_forgot_password(
            ClientId=settings.COGNITO_CLIENT_ID,
            Username=email,
            ConfirmationCode=code,
            Password=new_password,
        )
        return {"message": "Password reset successful"}
    except ClientError as e:
        raise HTTPException(400, e.response["Error"]["Message"])
