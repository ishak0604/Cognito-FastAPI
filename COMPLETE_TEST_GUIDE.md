# Complete Test Guide for AWS Cognito Authentication

This guide provides comprehensive testing scenarios for all Cognito authentication endpoints in the FastAPI application.

## Prerequisites

1. **Environment Setup:**
   - Update `env/.env` with your actual Cognito values:
     ```
     AWS_REGION=us-east-1
     COGNITO_USER_POOL_ID=your-actual-pool-id
     COGNITO_CLIENT_ID=your-actual-client-id
     USE_COGNITO=true
     ```

2. **Deploy Infrastructure:**
   ```bash
   ./deploy.sh
   ```

3. **Start Application:**
   ```bash
   cd docker
   docker-compose up -d
   ```

## Authentication Flow Overview

1. **Login URL** → User authenticates with Cognito → **Callback** → Receive tokens → Use tokens for authenticated requests

## Endpoint Test Scenarios

### 1. GET /api/v1/auth/login - Get Cognito Login URL

**Purpose:** Get the URL to redirect users to Cognito hosted UI for authentication.

**Test Case 1.1: Get Login URL (Success)**
```bash
curl -X GET "http://localhost:8000/api/v1/auth/login" \
  -H "accept: application/json"
```

**Expected Response:**
```json
{
  "login_url": "https://your-region.auth.amazoncognito.com/login?...",
  "message": "Redirect user to this URL for authentication"
}
```

**Test Case 1.2: Get Login URL with Custom Redirect URI**
```bash
curl -X GET "http://localhost:8000/api/v1/auth/login?redirect_uri=http://localhost:3000/callback" \
  -H "accept: application/json"
```

### 2. GET /api/v1/auth/callback - Handle Cognito OAuth Callback

**Purpose:** Process the authorization code from Cognito and exchange it for tokens.

**Test Case 2.1: Valid Authorization Code**
```bash
# First, complete the login flow in browser to get authorization code
# Then use the code in the callback URL
curl -X GET "http://localhost:8000/api/v1/auth/callback?code=AUTH_CODE_FROM_COGNITO" \
  -H "accept: application/json"
```

**Expected Response:**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJjdHkiOiJKV1QiLCJlbmMiOiJBMjU2R0NNIiwiYWxnIjoiUlNBLU9BRVAifQ...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_verified": true
  }
}
```

**Test Case 2.2: Invalid Authorization Code**
```bash
curl -X GET "http://localhost:8000/api/v1/auth/callback?code=INVALID_CODE" \
  -H "accept: application/json"
```

**Expected Response:**
```json
{
  "detail": "Failed to exchange authorization code for tokens"
}
```

**Test Case 2.3: Missing Authorization Code**
```bash
curl -X GET "http://localhost:8000/api/v1/auth/callback" \
  -H "accept: application/json"
```

**Expected Response:**
```json
{
  "detail": "Authorization code is required"
}
```

### 3. POST /api/v1/auth/refresh - Refresh Access Token

**Purpose:** Get a new access token using a valid refresh token.

**Test Case 3.1: Valid Refresh Token**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJjdHkiOiJKV1QiLCJlbmMiOiJBMjU2R0NNIiwiYWxnIjoiUlNBLU9BRVAifQ..."
  }'
```

**Expected Response:**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

**Test Case 3.2: Invalid Refresh Token**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "INVALID_REFRESH_TOKEN"
  }'
```

**Expected Response:**
```json
{
  "detail": "Invalid or expired refresh token"
}
```

**Test Case 3.3: Missing Refresh Token**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Expected Response:**
```json
{
  "detail": "Refresh token is required"
}
```

### 4. POST /api/v1/auth/logout - Logout User

**Purpose:** Revoke user tokens and clear session.

**Test Case 4.1: Valid Logout (Authenticated User)**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/logout" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

**Test Case 4.2: Logout Without Authentication**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/logout" \
  -H "Content-Type: application/json"
```

**Expected Response:**
```json
{
  "detail": "Not authenticated"
}
```

### 5. GET /api/v1/auth/me - Get Current User Information

**Purpose:** Retrieve information about the currently authenticated user.

**Test Case 5.1: Get User Info (Authenticated)**
```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "accept: application/json"
```

**Expected Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "is_verified": true,
  "authentication_method": "cognito",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**Test Case 5.2: Get User Info Without Authentication**
```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "accept: application/json"
```

**Expected Response:**
```json
{
  "detail": "Not authenticated"
}
```

### 6. GET /api/v1/auth/auth-status - Check Authentication Status

**Purpose:** Check if the current request is authenticated.

**Test Case 6.1: Check Status (Authenticated)**
```bash
curl -X GET "http://localhost:8000/api/v1/auth/auth-status" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "accept: application/json"
```

**Expected Response:**
```json
{
  "is_authenticated": true,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_verified": true,
    "authentication_method": "cognito",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

**Test Case 6.2: Check Status (Not Authenticated)**
```bash
curl -X GET "http://localhost:8000/api/v1/auth/auth-status" \
  -H "accept: application/json"
```

**Expected Response:**
```json
{
  "is_authenticated": false,
  "user": null
}
```

## Health Check Endpoint

### GET /health - Application Health Check

**Test Case: Health Check**
```bash
curl -X GET "http://localhost:8000/health" \
  -H "accept: application/json"
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Complete Authentication Flow Test

1. **Get Login URL**
2. **Authenticate in Browser** (manual step)
3. **Handle Callback** (get tokens)
4. **Use Access Token** for authenticated requests
5. **Refresh Token** when needed
6. **Check User Info**
7. **Logout**

## Error Scenarios to Test

- Expired tokens
- Invalid tokens
- Missing tokens
- Cognito service unavailable
- Database connection issues
- Invalid redirect URIs

## Performance Testing

- Concurrent authentication requests
- Token refresh under load
- Database query performance
- Cognito API rate limits

## Security Testing

- Token tampering
- SQL injection attempts
- XSS prevention
- CORS validation
- Rate limiting

## Monitoring

Check application logs for:
- Authentication success/failure
- Token refresh events
- User sync operations
- Error handling

## Cleanup

After testing, clean up:
```bash
# Stop containers
cd docker
docker-compose down

# Remove CloudFormation stack
aws cloudformation delete-stack --stack-name your-stack-name
