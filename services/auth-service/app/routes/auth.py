"""
Authentication routes for the Auth Service with Supabase integration.

This module provides API endpoints for user authentication, registration,
and session management using Supabase Auth.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm, HTTPBearer, HTTPAuthorizationCredentials

from app.models.user import UserCreate, UserLogin, UserResponse
from app.models.token import Token, RefreshToken
from app.services.auth_service import AuthService, security

router = APIRouter(tags=["Authentication"])
auth_service = AuthService()

@router.post(
    "/register", 
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Creates a new user account with email and password"
)
async def register(
    user_data: UserCreate,
    request: Request
):
    """
    Register a new user with enhanced security.
    
    This endpoint:
    - Validates input data
    - Checks for existing users
    - Creates a new user in Supabase Auth
    - Sets up a user profile
    - Returns a new session
    
    Args:
        user_data: User registration data
        request: FastAPI request object for security context
        
    Returns:
        dict: User data and session information
    """
    return await auth_service.register_user(user_data, request)

@router.post(
    "/login",
    response_model=dict,
    summary="Authenticate a user",
    description="Authenticates a user and returns session tokens"
)
async def login(
    user_data: UserLogin,
    request: Request
):
    """
    Authenticate a user with rate limiting.
    
    This endpoint:
    - Validates credentials against Supabase Auth
    - Implements rate limiting to prevent brute force
    - Returns access and refresh tokens
    - Logs authentication attempts
    
    Args:
        user_data: User login credentials
        request: FastAPI request object for security context
        
    Returns:
        dict: Session information including tokens
    """
    return await auth_service.login_user(user_data, request)

@router.post(
    "/token",
    response_model=dict,
    include_in_schema=False  # Hide from OpenAPI as it's for OAuth2 compatibility
)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None
):
    """
    OAuth2 compatible token login.
    
    This endpoint provides compatibility with OAuth2 clients.
    
    Args:
        form_data: OAuth2 form data with username/password
        request: FastAPI request object
        
    Returns:
        dict: Token response in OAuth2 format
    """
    user_data = UserLogin(email=form_data.username, password=form_data.password)
    result = await auth_service.login_user(user_data, request)
    
    # Format response to match OAuth2 spec
    return {
        "access_token": result["session"]["access_token"],
        "refresh_token": result["session"]["refresh_token"],
        "token_type": "bearer",
        "expires_in": result["session"]["expires_in"],
        "user": result["user"]
    }

@router.post(
    "/refresh",
    response_model=dict,
    summary="Refresh access token",
    description="Get a new access token using a refresh token"
)
async def refresh_token(refresh_data: RefreshToken):
    """
    Refresh an expired access token.
    
    Args:
        refresh_data: Contains the refresh token
        
    Returns:
        dict: New access and refresh tokens
    """
    return await auth_service.refresh_session(refresh_data.refresh_token)

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get the currently authenticated user's profile"
)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get the current authenticated user's profile.
    
    This endpoint requires a valid access token in the Authorization header.
    
    Returns:
        UserResponse: The authenticated user's profile data
    """
    return await auth_service.get_current_user(credentials)

@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout current user",
    description="Invalidates the current session"
)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Log out the current user.
    
    This will invalidate the current access token.
    
    Returns:
        None: 204 No Content on success
    """
    # In a real implementation, you would add the token to a blacklist
    # or use Supabase's sign_out method if available
    return None

@router.post(
    "/password/update",
    status_code=status.HTTP_200_OK,
    summary="Update user password",
    description="Update the current user's password"
)
async def update_password(
    current_password: str,
    new_password: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Update the current user's password.
    
    Args:
        current_password: Current password for verification
        new_password: New password to set
        
    Returns:
        dict: Success message
    """
    # Get user ID from token
    token_data = await auth_service.validate_token(credentials.credentials)
    return await auth_service.update_user_password(
        current_password=current_password,
        new_password=new_password,
        user_id=token_data["user_id"]
    )
