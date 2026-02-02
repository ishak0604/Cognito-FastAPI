import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException
from app.database import SessionLocal
from app.models.user import User
from app.core.config import settings

# Cognito client
client = boto3.client("cognito-idp", region_name=settings.AWS_REGION)

# ---------------------- UTILITY: SYNC USERS ----------------------
def sync_cognito_users_to_db():
    """
    Sync all users from Cognito User Pool into the local database.
    """
    session = SessionLocal()
    try:
        response = client.list_users(UserPoolId=settings.COGNITO_USER_POOL_ID)

        for u in response.get("Users", []):
            user_id = u["Username"]
            email_attr = next((attr["Value"] for attr in u["Attributes"] if attr["Name"] == "email"), "")
            role_attr = "user"  # default role

            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                user = User(id=user_id, email=email_attr, role=role_attr)
                session.add(user)
            else:
                # Update email/role if changed
                user.email = email_attr
                user.role = role_attr

        session.commit()
    except ClientError as e:
        raise HTTPException(500, f"Cognito sync failed: {e.response['Error']['Message']}")
    finally:
        session.close()


# ---------------------- SIGNUP ----------------------
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


# ---------------------- CONFIRM SIGNUP ----------------------
def confirm_signup(email: str, otp: str):
    db = SessionLocal()
    try:
        client.confirm_sign_up(
            ClientId=settings.COGNITO_CLIENT_ID,
            Username=email,
            ConfirmationCode=otp,
        )

        # Get user sub from Cognito
        user = client.admin_get_user(
            UserPoolId=settings.COGNITO_USER_POOL_ID,
            Username=email,
        )
        sub = next(attr["Value"] for attr in user["UserAttributes"] if attr["Name"] == "sub")

        # Create local DB user if not exists
        if not db.query(User).filter_by(id=sub).first():
            db.add(User(id=sub, email=email))
            db.commit()

        return {"message": "Account verified successfully"}
    except ClientError as e:
        db.rollback()
        raise HTTPException(400, e.response["Error"]["Message"])
    finally:
        db.close()


# ---------------------- LOGIN ----------------------
def login(email: str, password: str):
    try:
        res = client.initiate_auth(
            ClientId=settings.COGNITO_CLIENT_ID,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={"USERNAME": email, "PASSWORD": password},
        )
        result = res["AuthenticationResult"]
        return {
            "access_token": result["AccessToken"],
            "refresh_token": result.get("RefreshToken"),
            "id_token": result["IdToken"],
            "expires_in": result["ExpiresIn"],
        }
    except ClientError as e:
        msg = e.response["Error"]["Message"]
        if "User is not confirmed" in msg:
            raise HTTPException(403, "User not confirmed. Verify OTP first.")
        if "security token" in msg.lower():
            raise HTTPException(401, "AWS credentials expired. Update .env")
        raise HTTPException(401, msg)


# ---------------------- FORGOT PASSWORD ----------------------
def forgot_password(email: str):
    try:
        client.forgot_password(ClientId=settings.COGNITO_CLIENT_ID, Username=email)
        return {"message": "Reset code sent"}
    except ClientError as e:
        raise HTTPException(400, e.response["Error"]["Message"])


# ---------------------- RESET PASSWORD ----------------------
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
