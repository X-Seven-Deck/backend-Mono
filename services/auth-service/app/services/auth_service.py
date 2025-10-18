"""
Authentication service for the Auth Service using Supabase Auth.

This service provides authentication and authorization functionality
using Supabase Auth with enterprise-grade security practices.
"""

import logging
from typing import Any, Dict, Optional
import sys
import os

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings
from app.models.user import UserCreate, UserLogin, UserResponse

# Add shared directory to path
file_dir = os.path.dirname(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(file_dir))))
shared_path = os.path.join(project_root, 'shared')
sys.path.append(shared_path)
from libs.supabase_client import SupabaseManager, get_supabase_client

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


class AuthService:
    """Authentication and session management powered by Supabase Auth."""

    def __init__(self) -> None:
        # Service key client for privileged operations
        self.supabase = SupabaseManager(use_service_key=True)
        # Regular client for token validation and user context
        self.supabase_client = get_supabase_client()

    async def register_user(
        self,
        user_data: UserCreate,
        request: Optional[Request] = None,
    ) -> Dict[str, Any]:
        """Register a new user and return Supabase session details."""
        try:
            # First, sign up the user with Supabase Auth
            auth_response = await self.supabase.sign_up(
                email=user_data.email,
                password=user_data.password,
                user_data={
                    "email": user_data.email,
                    "full_name": user_data.full_name,
                    "phone_number": user_data.phone_number,
                },
            )

            if not auth_response.get("user"):
                raise ValueError("Failed to register user")
                
            user_id = auth_response["user"]["id"]
            
            # Note: User profile in public.users should be created by database trigger
            # or handled by Supabase Auth automatically
            # Skipping manual insert to avoid RLS policy violations
            
            # Create a default business for every user (if RPC exists)
            try:
                business_data = {
                    "name": f"{user_data.full_name}'s Business",
                    "owner_id": user_id,
                    "email": user_data.email,
                    "phone": user_data.phone_number
                }
                await self.supabase_client.rpc(
                    'create_business_with_owner',
                    {
                        'business_data': business_data,
                        'owner_id': user_id
                    }
                ).execute()
            except Exception as e:
                # Log but don't fail registration if business creation fails
                logger.warning(f"Could not create default business for user {user_id}: {e}")

            return auth_response

        except ValueError as exc:  # SupabaseManager will raise ValueError on failure
            logger.warning("Registration failed for %s: %s", user_data.email, exc)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc
        except Exception as exc:  # pragma: no cover - unexpected
            logger.error("Unexpected registration error: %s", exc, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to register user",
            ) from exc

    async def login_user(
        self,
        user_data: UserLogin,
        request: Optional[Request] = None,
    ) -> Dict[str, Any]:
        """Authenticate a user via Supabase and return session information."""
        try:
            auth_response = await self.supabase.sign_in(
                email=user_data.email,
                password=user_data.password,
                remember_me=user_data.remember_me,
            )

            if not auth_response.get("user"):
                raise ValueError("Invalid email or password")

            return auth_response

        except ValueError as exc:
            logger.warning("Login failed for %s: %s", user_data.email, exc)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            ) from exc
        except Exception as exc:  # pragma: no cover - unexpected
            logger.error("Unexpected login error for %s: %s", user_data.email, exc, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred during authentication",
            ) from exc

    async def refresh_session(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access credentials using a Supabase refresh token."""
        try:
            return await self.supabase.refresh_session(refresh_token)

        except ValueError as exc:
            logger.warning("Refresh token rejected: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            ) from exc
        except Exception as exc:  # pragma: no cover - unexpected
            logger.error("Unexpected session refresh error: %s", exc, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            ) from exc

    async def get_current_user(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(security),
    ) -> Dict[str, Any]:
        """
        Get the current authenticated user with their business roles.
        
        Args:
            credentials: The HTTP authorization credentials.
            
        Returns:
            The current user's data including business roles.
            
        Raises:
            HTTPException: If the token is invalid or the user is not found.
        """
        try:
            if not credentials:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
                
            # Verify the token with Supabase
            token = credentials.credentials
            
            # Get user from token using Supabase Auth
            try:
                response = self.supabase.client.auth.get_user(token)
                if not response or not response.user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Could not validate credentials",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                user_data = response.user
            except Exception as e:
                logger.error(f"Token validation failed: {e}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
                
            # Enterprise-grade: Return user data from token, profile lookup is optional
            # This ensures tokens work even if profile sync is delayed
            user = {
                "id": str(user_data.id),
                "email": user_data.email,
                "user_metadata": user_data.user_metadata or {}
            }
            
            # Try to get additional profile data, but don't fail if unavailable
            try:
                profile = await self.supabase.get_user(user_data.id, include_roles=True)
                if profile:
                    user.update(profile)
            except Exception as e:
                logger.warning(f"Profile lookup failed, using token data only: {e}")
            
            # Return user data
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in get_current_user: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    async def update_user_password(
        self,
        current_password: str,
        new_password: str,
        user_id: str,
    ) -> Dict[str, str]:
        """Update a user's password using the Supabase admin API."""
        try:
            # Verify current password by attempting a sign-in with email lookup
            profile = await self.supabase.get_user_profile(user_id)
            if not profile:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User profile not found",
                )

            email = profile.get("email")
            if not email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User email unavailable",
                )

            try:
                await self.supabase.sign_in(email=email, password=current_password)
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is incorrect",
                ) from exc

            result = self.supabase.client.auth.admin.update_user_by_id(
                user_id,
                {"password": new_password},
            )

            if not result or not getattr(result, "user", None):
                raise ValueError("Password update failed")

            # Invalidate other sessions for security
            try:
                self.supabase.client.auth.admin.sign_out(user_id)
            except Exception as exc:  # pragma: no cover - best effort only
                logger.warning("Failed to sign out other sessions for %s: %s", user_id, exc)

            return {"message": "Password updated successfully"}

        except HTTPException:
            raise
        except ValueError as exc:
            logger.warning("Password update failed for %s: %s", user_id, exc)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc
        except Exception as exc:  # pragma: no cover - unexpected
            logger.error("Unexpected password update error for %s: %s", user_id, exc, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password",
            ) from exc

    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Decode and validate a Supabase JWT token."""
        try:
            auth_user = self.supabase_client.auth.get_user(token)

            if not auth_user or not getattr(auth_user, "user", None):
                raise ValueError("Invalid token")

            user_profile = await self.supabase.get_user_profile(auth_user.user.id)

            return {
                "user_id": auth_user.user.id,
                "email": auth_user.user.email,
                "role": (user_profile or {}).get("role", "customer"),
                "email_confirmed": bool(getattr(auth_user.user, "email_confirmed_at", None)),
                "exp": getattr(auth_user.user, "exp", None),
            }

        except ValueError as exc:
            logger.warning("Token validation failed: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            ) from exc
        except Exception as exc:  # pragma: no cover - unexpected
            logger.error("Unexpected token validation error: %s", exc, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            ) from exc
