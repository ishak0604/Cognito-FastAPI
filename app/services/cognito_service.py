import boto3
from typing import Optional, Dict, Any
from botocore.exceptions import ClientError
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class CognitoService:
    """AWS Cognito service for authentication"""
    
    def __init__(self):
        if not settings.USE_COGNITO:
            return
        self.client = boto3.client('cognito-idp', region_name=settings.AWS_REGION)
        self.user_pool_id = settings.COGNITO_USER_POOL_ID
        self.client_id = settings.COGNITO_CLIENT_ID
    
    def authenticate(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate user with Cognito"""
        try:
            response = self.client.admin_initiate_auth(
                UserPoolId=self.user_pool_id,
                ClientId=self.client_id,
                AuthFlow='ADMIN_NO_SRP_AUTH',
                AuthParameters={'USERNAME': email, 'PASSWORD': password}
            )
            
            auth_result = response['AuthenticationResult']
            return {
                'success': True,
                'access_token': auth_result['AccessToken'],
                'expires_in': auth_result['ExpiresIn']
            }
        except ClientError as e:
            return {'success': False, 'message': e.response['Error']['Message']}
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return user info"""
        try:
            response = self.client.get_user(AccessToken=token)
            return {
                'email': next(attr['Value'] for attr in response['UserAttributes'] if attr['Name'] == 'email'),
                'sub': response['Username']
            }
        except ClientError:
            return None

# Global instance
cognito_service = CognitoService()