"""
User routes for the Auth Service.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.models.user import UserResponse, UserUpdate
from app.services.auth_service import AuthService
from app.services.user_service import UserService

router = APIRouter()
auth_service = AuthService()
user_service = UserService()

@router.get("", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: UserResponse = Depends(auth_service.get_current_user),
):
    """
    List users.
    
    Args:
        skip: Number of users to skip.
        limit: Maximum number of users to return.
        current_user: Current authenticated user.
        
    Returns:
        List of users.
    """
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
        
    return await user_service.list_users(skip, limit)

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: UserResponse = Depends(auth_service.get_current_user),
):
    """
    Get a user by ID.
    
    Args:
        user_id: User ID.
        current_user: Current authenticated user.
        
    Returns:
        User data.
    """
    # Check if user is admin or the requested user
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
        
    return await user_service.get_user(user_id)

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    current_user: UserResponse = Depends(auth_service.get_current_user),
):
    """
    Update a user.
    
    Args:
        user_id: User ID.
        user_data: User update data.
        current_user: Current authenticated user.
        
    Returns:
        Updated user data.
    """
    # Check if user is admin or the requested user
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
        
    # If not admin, prevent role change
    if current_user.role != "admin" and user_data.role is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to change role",
        )
        
    return await user_service.update_user(user_id, user_data)

@router.delete("/{user_id}")
async def delete_user(
    user_id: UUID,
    current_user: UserResponse = Depends(auth_service.get_current_user),
):
    """
    Delete a user.
    
    Args:
        user_id: User ID.
        current_user: Current authenticated user.
        
    Returns:
        Success message.
    """
    # Check if user is admin or the requested user
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
        
    return await user_service.delete_user(user_id)
