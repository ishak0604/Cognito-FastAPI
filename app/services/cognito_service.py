import boto3
from typing import Optional, Dict, Any
from botocore.exceptions import ClientError
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class CognitoService:
    """AWS Cognito service for authentication and user management"""

    def __init__(self):
        if not settings.USE_COGNITO:
            return
        self.client = boto3.client('cognito-idp', region_name=settings.AWS_REGION)
        self.user_pool_id = settings.COGNITO_USER_POOL_ID
        self.client_id = settings.COGNITO_CLIENT_ID

    def sign_up(self, email: str, password: str) -> Dict[str, Any]:
        """Sign up a new user with Cognito"""
        try:
            response = self.client.sign_up(
                ClientId=self.client_id,
                Username=email,
                Password=password,
                UserAttributes=[
                    {
                        'Name': 'email',
                        'Value': email
                    }
                ]
            )
            return {
                'success': True,
                'message': 'User signed up successfully. Please check your email for verification code.',
                'user_id': response['UserSub'],
                'email': email
            }
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'UsernameExistsException':
                return {'success': False, 'message': 'User already exists'}
            elif error_code == 'InvalidPasswordException':
                return {'success': False, 'message': 'Password does not meet requirements'}
            elif error_code == 'InvalidParameterException':
                return {'success': False, 'message': 'Invalid email format'}
            else:
                return {'success': False, 'message': f'Signup failed: {e.response["Error"]["Message"]}'}

    def confirm_sign_up(self, email: str, confirmation_code: str) -> Dict[str, Any]:
        """Confirm user signup with verification code"""
        try:
            self.client.confirm_sign_up(
                ClientId=self.client_id,
                Username=email,
                ConfirmationCode=confirmation_code
            )

            # After confirmation, initiate auth to get tokens
            auth_result = self.admin_initiate_auth(email, "")
            if auth_result['success']:
                return {
                    'success': True,
                    'message': 'Account verified successfully',
                    'access_token': auth_result['access_token'],
                    'refresh_token': auth_result.get('refresh_token', ''),
                    'user': {
                        'email': email,
                        'email_verified': True
                    }
                }
            else:
                return {
                    'success': True,
                    'message': 'Account verified successfully. Please login to continue.',
                    'user': {
                        'email': email,
                        'email_verified': True
                    }
                }
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'CodeMismatchException':
                return {'success': False, 'message': 'Invalid verification code'}
            elif error_code == 'ExpiredCodeException':
                return {'success': False, 'message': 'Verification code has expired'}
            elif error_code == 'NotAuthorizedException':
                return {'success': False, 'message': 'User is already confirmed'}
            else:
                return {'success': False, 'message': f'Confirmation failed: {e.response["Error"]["Message"]}'}

    def resend_confirmation_code(self, email: str) -> Dict[str, Any]:
        """Resend confirmation code"""
        try:
            self.client.resend_confirmation_code(
                ClientId=self.client_id,
                Username=email
            )
            return {
                'success': True,
                'message': 'Verification code sent successfully'
            }
        except ClientError as e:
            return {'success': False, 'message': f'Failed to resend code: {e.response["Error"]["Message"]}'}

    def admin_initiate_auth(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate user with Cognito (admin method)"""
        try:
            response = self.client.admin_initiate_auth(
                UserPoolId=self.user_pool_id,
                ClientId=self.client_id,
                AuthFlow='ADMIN_NO_SRP_AUTH',
                AuthParameters={
                    'USERNAME': email,
                    'PASSWORD': password
                }
            )

            auth_result = response.get('AuthenticationResult', {})
            return {
                'success': True,
                'access_token': auth_result.get('AccessToken', ''),
                'refresh_token': auth_result.get('RefreshToken', ''),
                'expires_in': auth_result.get('ExpiresIn', 3600)
            }
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NotAuthorizedException':
                return {'success': False, 'message': 'Invalid email or password'}
            elif error_code == 'UserNotFoundException':
                return {'success': False, 'message': 'User not found'}
            elif error_code == 'UserNotConfirmedException':
                return {'success': False, 'message': 'Please verify your email first'}
            else:
                return {'success': False, 'message': f'Login failed: {e.response["Error"]["Message"]}'}

    def forgot_password(self, email: str) -> Dict[str, Any]:
        """Initiate forgot password flow"""
        try:
            self.client.forgot_password(
                ClientId=self.client_id,
                Username=email
            )
            return {
                'success': True,
                'message': 'Password reset code sent to your email'
            }
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'UserNotFoundException':
                return {'success': False, 'message': 'User not found'}
            elif error_code == 'InvalidParameterException':
                return {'success': False, 'message': 'Invalid email format'}
            else:
                return {'success': False, 'message': f'Failed to send reset code: {e.response["Error"]["Message"]}'}

    def confirm_forgot_password(self, email: str, confirmation_code: str, new_password: str) -> Dict[str, Any]:
        """Confirm forgot password with new password"""
        try:
            self.client.confirm_forgot_password(
                ClientId=self.client_id,
                Username=email,
                ConfirmationCode=confirmation_code,
                Password=new_password
            )
            return {
                'success': True,
                'message': 'Password reset successfully'
            }
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'CodeMismatchException':
                return {'success': False, 'message': 'Invalid reset code'}
            elif error_code == 'ExpiredCodeException':
                return {'success': False, 'message': 'Reset code has expired'}
            elif error_code == 'InvalidPasswordException':
                return {'success': False, 'message': 'Password does not meet requirements'}
            else:
                return {'success': False, 'message': f'Password reset failed: {e.response["Error"]["Message"]}'}

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return user info"""
        try:
            response = self.client.get_user(AccessToken=token)
            return {
                'email': next(attr['Value'] for attr in response['UserAttributes'] if attr['Name'] == 'email'),
                'sub': response['Username'],
                'email_verified': next((attr['Value'] for attr in response['UserAttributes'] if attr['Name'] == 'email_verified'), 'false') == 'true'
            }
        except ClientError:
            return None

    def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get user information from access token"""
        return self.verify_token(access_token)

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        try:
            response = self.client.admin_initiate_auth(
                UserPoolId=self.user_pool_id,
                ClientId=self.client_id,
                AuthFlow='REFRESH_TOKEN_AUTH',
                AuthParameters={
                    'REFRESH_TOKEN': refresh_token
                }
            )

            auth_result = response.get('AuthenticationResult', {})
            return {
                'success': True,
                'access_token': auth_result.get('AccessToken', ''),
                'expires_in': auth_result.get('ExpiresIn', 3600)
            }
        except ClientError as e:
            return {'success': False, 'message': f'Token refresh failed: {e.response["Error"]["Message"]}'}

# Global instance
cognito_service = CognitoService()
