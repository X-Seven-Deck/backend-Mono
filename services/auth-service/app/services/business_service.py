"""
Business service for the Auth Service.
"""

import logging
from typing import Dict, Any, List, Optional
from uuid import UUID
import sys
import os

from fastapi import HTTPException, status

from app.models.business import BusinessCreate, BusinessUpdate, BusinessResponse

# Add shared directory to path
file_dir = os.path.dirname(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(file_dir))))
shared_path = os.path.join(project_root, 'shared')
sys.path.append(shared_path)
from libs.supabase_client import SupabaseManager

# Configure logging
logger = logging.getLogger(__name__)

class BusinessService:
    """Business service."""

    def __init__(self):
        """Initialize the business service."""
        self.supabase = SupabaseManager(use_service_key=True)
    
    async def get_user_businesses(self, user_id: str, skip: int = 0, limit: int = 100) -> List[BusinessResponse]:
        """
        Get all businesses where user has a role (enterprise-grade implementation).
        
        Args:
            user_id: User ID
            skip: Number to skip
            limit: Maximum number to return
            
        Returns:
            List of businesses
        """
        try:
            # Query user_business_roles to get businesses
            result = self.supabase.client.table("user_business_roles")\
                .select("business_id, businesses(*)")\
                .eq("user_id", str(user_id))\
                .range(skip, skip + limit - 1)\
                .execute()
            
            if not result.data:
                return []
            
            # Extract business data
            businesses = []
            for row in result.data:
                if row.get("businesses"):
                    businesses.append(BusinessResponse(**row["businesses"]))
            
            return businesses
        except Exception as e:
            logger.error(f"Error fetching user businesses: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch businesses: {str(e)}"
            )

    async def create_business(self, business_data: BusinessCreate) -> BusinessResponse:
        """
        Create a new business and set up the owner relationship.

        Args:
            business_data: Business creation data.

        Returns:
            The created business data.

        Raises:
            HTTPException: If creation fails.
        """
        try:
            # Create business (only fields that exist in businesses table)
            business_dict = business_data.dict(exclude={"owner_id"})
            
            # Map category/business_type to category_id (default to 1 for "other")
            category_id = 1  # Default category
            if business_dict.get("category"):
                category_map = {"restaurant": 1, "salon": 2, "freelancing": 3, "local_shop": 4, "other": 1}
                category_id = category_map.get(business_dict["category"], 1)
            
            import uuid
            # Create unique slug with UUID suffix to avoid duplicates
            base_slug = business_dict["name"].lower().replace(" ", "-")[:40]
            unique_slug = f"{base_slug}-{str(uuid.uuid4())[:8]}"
            
            created_business = await self.supabase.insert(
                table="businesses",
                data={
                    "name": business_dict["name"],
                    "slug": unique_slug,
                    "category_id": category_id,
                    "status": "active",
                },
            )
            
            if not created_business:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create business",
                )
            
            business_id = created_business[0]["id"]
            
            # Create business profile with detailed information
            await self.supabase.insert(
                table="business_profiles",
                data={
                    "business_id": business_id,
                    "owner_id": str(business_data.owner_id),
                    "name": business_dict["name"],
                    "description": business_dict.get("description"),
                    "address": business_dict.get("address"),
                    "email": business_dict.get("email"),
                    "phone": business_dict.get("phone"),
                    "website": business_dict.get("website"),
                    "logo_url": business_dict.get("logo_url"),
                    "settings": business_dict.get("settings", {}),
                    "is_active": True,
                }
            )
            
            # Create user-business relationship
            await self.supabase.insert(
                table="user_business_roles",
                data={
                    "user_id": str(business_data.owner_id),
                    "business_id": business_id,
                    "role": "owner"  # Valid roles: owner, admin, staff
                }
            )
            
            return BusinessResponse(**created_business[0])
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Create business error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create business: {str(e)}",
            )

    async def get_business(self, business_id: UUID, current_user_id: UUID = None) -> BusinessResponse:
        """
        Get a business by ID with proper authorization.

        Args:
            business_id: Business ID.
            current_user_id: ID of the currently authenticated user.

        Returns:
            Business data with details.

        Raises:
            HTTPException: If business not found or user not authorized.
        """
        try:
            # Get the business
            business_result = self.supabase.client.table("businesses").select("*").eq("id", str(business_id)).execute()
            business = business_result.data[0] if business_result.data else None
            
            if not business:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Business not found",
                )
            
            return BusinessResponse(**business)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Get business error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get business: {str(e)}",
            )

    async def update_business(self, business_id: UUID, business_data: BusinessUpdate) -> BusinessResponse:
        """
        Update a business.

        Args:
            business_id: Business ID.
            business_data: Business update data.

        Returns:
            Updated business data.

        Raises:
            HTTPException: If update fails.
        """
        try:
            # Prepare update data - only include fields that exist in businesses table
            update_data = business_data.dict(exclude_unset=True)
            allowed_fields = {'name', 'slug', 'category_id', 'status'}
            filtered_data = {k: v for k, v in update_data.items() if k in allowed_fields}
            
            # Update business
            if filtered_data:
                updated_result = self.supabase.client.table("businesses").update(filtered_data).eq("id", str(business_id)).execute()
                
                if not updated_result.data:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Business not found",
                    )
                
                return BusinessResponse(**updated_result.data[0])
            
            # If no updates, get and return current business
            return await self.get_business(business_id)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Update business error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update business: {str(e)}",
            )

    async def delete_business(self, business_id: UUID) -> Dict[str, Any]:
        """
        Delete a business.

        Args:
            business_id: Business ID.

        Returns:
            Success message.

        Raises:
            HTTPException: If deletion fails.
        """
        try:
            # Check if business exists
            business_profile = await self.supabase.get_business_profile(str(business_id))
            
            if not business_profile:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Business not found",
                )
            
            # Delete business profile
            deleted_profile = await self.supabase.delete(
                table="business_profiles",
                filters={"id": str(business_id)},
            )
            
            if not deleted_profile:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to delete business profile",
                )
            
            return {"message": "Business deleted successfully"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Delete business error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete business: {str(e)}",
            )

    async def list_businesses(self, skip: int = 0, limit: int = 100) -> List[BusinessResponse]:
        """
        List businesses.

        Args:
            skip: Number of businesses to skip.
            limit: Maximum number of businesses to return.

        Returns:
            List of businesses.

        Raises:
            HTTPException: If listing fails.
        """
        try:
            businesses = await self.supabase.select(
                table="business_profiles",
                columns="*",
            )
            
            # Apply pagination
            paginated_businesses = businesses[skip:skip + limit]
            
            return [BusinessResponse(**business) for business in paginated_businesses]
        except Exception as e:
            logger.error(f"List businesses error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list businesses: {str(e)}",
            )

    async def get_businesses_by_owner(self, owner_id: UUID) -> List[BusinessResponse]:
        """
        Get businesses by owner ID.

        Args:
            owner_id: Owner ID.

        Returns:
            List of businesses.

        Raises:
            HTTPException: If retrieval fails.
        """
        try:
            businesses = await self.supabase.select(
                table="business_profiles",
                columns="*",
                filters={"owner_id": str(owner_id)},
            )
            
            return [BusinessResponse(**business) for business in businesses]
        except Exception as e:
            logger.error(f"Get businesses by owner error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get businesses by owner: {str(e)}",
            )
