"""
User service for the Auth Service.
"""

import logging
from typing import Dict, Any, List, Optional
from uuid import UUID
import sys
import os

from fastapi import HTTPException, status

from app.models.user import UserUpdate, UserResponse

# Add shared directory to path
file_dir = os.path.dirname(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(file_dir))))
shared_path = os.path.join(project_root, 'shared')
sys.path.append(shared_path)
from libs.supabase_client import SupabaseManager

# Configure logging
logger = logging.getLogger(__name__)

class UserService:
    """User service."""

    def __init__(self):
        """Initialize the user service."""
        self.supabase = SupabaseManager()

    async def get_user(self, user_id: UUID) -> UserResponse:
        """
        Get a user by ID.

        Args:
            user_id: User ID.

        Returns:
            User data.

        Raises:
            HTTPException: If user not found.
        """
        try:
            user_profile = await self.supabase.get_user_profile(str(user_id))
            
            if not user_profile:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )
                
            return UserResponse(**user_profile)
        except Exception as e:
            logger.error(f"Get user error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get user: {str(e)}",
            )

    async def update_user(self, user_id: UUID, user_data: UserUpdate) -> UserResponse:
        """
        Update a user.

        Args:
            user_id: User ID.
            user_data: User update data.

        Returns:
            Updated user data.

        Raises:
            HTTPException: If update fails.
        """
        try:
            # Check if user exists
            user_profile = await self.supabase.get_user_profile(str(user_id))
            
            if not user_profile:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )
            
            # Prepare update data
            update_data = user_data.dict(exclude_unset=True)
            
            # Handle password update separately if provided
            if "password" in update_data and "confirm_password" in update_data:
                if update_data["password"] != update_data["confirm_password"]:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Passwords do not match",
                    )
                
                # Update password in Supabase Auth (would need admin privileges)
                # This would typically be handled by Supabase directly
                
                # Remove password fields from profile update
                update_data.pop("password", None)
                update_data.pop("confirm_password", None)
            
            # Update user profile
            if update_data:
                updated_profile = await self.supabase.update(
                    table="user_profiles",
                    data=update_data,
                    filters={"id": str(user_id)},
                )
                
                if not updated_profile:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to update user profile",
                    )
                
                return UserResponse(**updated_profile[0])
            
            # If no updates were made, return the current profile
            return UserResponse(**user_profile)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Update user error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update user: {str(e)}",
            )

    async def delete_user(self, user_id: UUID) -> Dict[str, Any]:
        """
        Delete a user.

        Args:
            user_id: User ID.

        Returns:
            Success message.

        Raises:
            HTTPException: If deletion fails.
        """
        try:
            # Check if user exists
            user_profile = await self.supabase.get_user_profile(str(user_id))
            
            if not user_profile:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )
            
            # Delete user profile
            deleted_profile = await self.supabase.delete(
                table="user_profiles",
                filters={"id": str(user_id)},
            )
            
            if not deleted_profile:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to delete user profile",
                )
            
            # Note: Deleting from auth.users would require admin privileges
            # This would typically be handled by Supabase directly or through admin API
            
            return {"message": "User deleted successfully"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Delete user error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete user: {str(e)}",
            )

    async def list_users(self, skip: int = 0, limit: int = 100) -> List[UserResponse]:
        """
        List users.

        Args:
            skip: Number of users to skip.
            limit: Maximum number of users to return.

        Returns:
            List of users.

        Raises:
            HTTPException: If listing fails.
        """
        try:
            # This would typically require admin privileges
            # For security, we might want to limit this to admins only
            users = await self.supabase.select(
                table="user_profiles",
                columns="*",
            )
            
            # Apply pagination
            paginated_users = users[skip:skip + limit]
            
            return [UserResponse(**user) for user in paginated_users]
        except Exception as e:
            logger.error(f"List users error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list users: {str(e)}",
            )
