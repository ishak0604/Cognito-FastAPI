import os
import base64
import logging
import requests
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID")
COGNITO_CLIENT_SECRET = os.getenv("COGNITO_CLIENT_SECRET")
COGNITO_DOMAIN = os.getenv("COGNITO_DOMAIN")  # e.g. https://<prefix>.auth.<region>.amazoncognito.com
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
COGNITO_REGION = os.getenv("COGNITO_REGION", "us-east-1")

# Helper: return Authorization header for client auth (Basic)
def _client_auth_header():
    if not COGNITO_CLIENT_ID or not COGNITO_CLIENT_SECRET:
        return {}
    client_creds = f"{COGNITO_CLIENT_ID}:{COGNITO_CLIENT_SECRET}"
    b64 = base64.b64encode(client_creds.encode()).decode()
    return {"Authorization": f"Basic {b64}"}

class CognitoService:
    def __init__(self):
        if not COGNITO_DOMAIN:
            raise RuntimeError("COGNITO_DOMAIN must be set")
        self.domain = COGNITO_DOMAIN.rstrip("/")

    def get_cognito_login_url(self, redirect_uri: str):
        # Construct the hosted UI authorization URL (authorization code flow)
        params = {
            "client_id": COGNITO_CLIENT_ID,
            "response_type": "code",
            "scope": "openid+email+profile",
            "redirect_uri": redirect_uri,
        }
        url = f"{self.domain}/oauth2/authorize?{urlencode(params)}"
        return url

    def exchange_code_for_tokens(self, code: str, redirect_uri: str):
        """
        Exchange authorization code for tokens via Cognito /oauth2/token.
        Returns parsed JSON containing access_token,id_token,refresh_token,expires_in,token_type
        """
        token_url = f"{self.domain}/oauth2/token"
        data = {
            "grant_type": "authorization_code",
            "client_id": COGNITO_CLIENT_ID,
            "code": code,
            "redirect_uri": redirect_uri
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        # Add client secret using HTTP Basic if present
        headers.update(_client_auth_header())
        r = requests.post(token_url, data=urlencode(data), headers=headers, timeout=10)
        try:
            r.raise_for_status()
        except Exception as e:
            logger.error("Token exchange failed: %s %s", r.status_code, r.text)
            raise
        return r.json()

    def get_userinfo(self, access_token: str):
        """
        Retrieve user info from /oauth2/userInfo endpoint.
        """
        userinfo_url = f"{self.domain}/oauth2/userInfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        r = requests.get(userinfo_url, headers=headers, timeout=10)
        r.raise_for_status()
        return r.json()

    def handle_cognito_user_sync(self, user_info: dict, db):
        """
        Sync Cognito user info to your DB. Adapt to your models.
        - user_info typically contains 'sub', 'email', 'email_verified', 'name' etc.
        Return the DB user instance.
        """
        # Example pseudo-code (adapt for your models and session):
        # from app.database.models.user import User
        # user = db.query(User).filter(User.cognito_sub == user_info["sub"]).first()
        # if not user:
        #     user = User(email=user_info.get("email"), cognito_sub=user_info.get("sub"), is_verified=user_info.get("email_verified", False))
        #     db.add(user)
        # else:
        #     user.email = user_info.get("email", user.email)
        #     user.is_verified = user_info.get("email_verified", user.is_verified)
        # db.commit()
        # return user
        # If you don't want DB sync, simply return user_info dict.
        return user_info

# Export a singleton
cognito_service = CognitoService()