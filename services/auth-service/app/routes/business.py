"""
Business routes for the Auth Service.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.models.user import UserResponse
from app.models.business import BusinessCreate, BusinessResponse, BusinessUpdate
from app.services.auth_service import AuthService
from app.services.business_service import BusinessService

router = APIRouter()
auth_service = AuthService()
business_service = BusinessService()

@router.post("", response_model=BusinessResponse, status_code=status.HTTP_201_CREATED)
async def create_business(
    business_data: BusinessCreate,
    current_user: dict = Depends(auth_service.get_current_user),
):
    """
    Create a new business.
    
    Args:
        business_data: Business creation data.
        current_user: Current authenticated user.
        
    Returns:
        The created business data.
    """
    # Ensure the user has a valid ID
    if not current_user or 'id' not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Add the current user as the owner
    business_data.owner_id = current_user['id']
    
    return await business_service.create_business(business_data)

@router.get("", response_model=List[BusinessResponse])
async def list_businesses(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: dict = Depends(auth_service.get_current_user),
):
    """
    List businesses that the current user has access to.
    
    Args:
        skip: Number of businesses to skip.
        limit: Maximum number of businesses to return.
        current_user: Current authenticated user.
        
    Returns:
        List of businesses.
    """
    # Enterprise-grade: Query user's businesses from database directly
    user_id = current_user.get('id')
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user session"
        )
    
    # Get businesses where user has a role
    return await business_service.get_user_businesses(user_id, skip, limit)

@router.get("/owner/{owner_id}", response_model=List[BusinessResponse])
async def get_businesses_by_owner(
    owner_id: str,
    current_user: dict = Depends(auth_service.get_current_user),
):
    """
    Get businesses by owner ID.
    
    Args:
        owner_id: Owner ID.
        current_user: Current authenticated user.
        
    Returns:
        List of businesses owned by the specified user.
    """
    # Check if user is admin or the requested owner
    if current_user.get('role') != 'admin' and current_user.get('id') != owner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Get businesses where the user has an owner role
    businesses = [
        business for business in (current_user.get('businesses') or [])
        if business.get('role') == 'owner' and business.get('user_id') == owner_id
    ]
    
    # Get full business details
    result = []
    for business in businesses:
        business_detail = await business_service.get_business(business['id'])
        if business_detail:
            result.append(business_detail)
    
    return result

@router.get("/{business_id}", response_model=BusinessResponse)
async def get_business(
    business_id: str,
    current_user: dict = Depends(auth_service.get_current_user)
):
    """
    Get a business by ID with proper authorization.
    
    Args:
        business_id: Business ID.
        current_user: Current authenticated user.
        
    Returns:
        Business data if the user has access.
        
    Raises:
        HTTPException: If the business is not found or the user doesn't have access.
    """
    # Enterprise-grade: Check if user has access by querying database
    user_id = current_user.get('id')
    user_businesses = await business_service.get_user_businesses(user_id, 0, 100)
    
    has_access = any(str(b.id) == str(business_id) for b in user_businesses)
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this business"
        )
    
    # Get the business with the current user's ID for authorization
    return await business_service.get_business(business_id, current_user_id=current_user.get('id'))

@router.put("/{business_id}", response_model=BusinessResponse)
async def update_business(
    business_id: str,
    business_data: BusinessUpdate,
    current_user: dict = Depends(auth_service.get_current_user),
):
    """
    Update a business.
    
    Args:
        business_id: Business ID.
        business_data: Business update data.
        current_user: Current authenticated user.
        
    Returns:
        Updated business data.
        
    Raises:
        HTTPException: If the business is not found or the user doesn't have permission.
    """
    # Enterprise-grade: Check permissions by querying database
    user_id = current_user.get('id')
    user_businesses = await business_service.get_user_businesses(user_id, 0, 100)
    
    has_permission = any(str(b.id) == str(business_id) for b in user_businesses)
    
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this business"
        )
    
    # Proceed with the update
    return await business_service.update_business(business_id, business_data)

@router.delete("/{business_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_business(
    business_id: str,
    current_user: dict = Depends(auth_service.get_current_user),
):
    """
    Delete a business.
    
    Args:
        business_id: Business ID.
        current_user: Current authenticated user.
        
    Returns:
        None
        
    Raises:
        HTTPException: If the business is not found or the user doesn't have permission.
    """
    # Check if user is admin or business owner
    is_owner = False
    
    # Check user's role in this business
    for business in (current_user.get('businesses') or []):
        if business.get('id') == business_id:
            if business.get('role') == 'owner':
                is_owner = True
            break
    
    # Only allow deletion by business owners or admins
    if not is_owner and current_user.get('role') != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only business owners or admins can delete a business"
        )
    
    # Get the business to ensure it exists
    business = await business_service.get_business(business_id)
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found"
        )
    
    # Proceed with deletion
    await business_service.delete_business(business_id)
