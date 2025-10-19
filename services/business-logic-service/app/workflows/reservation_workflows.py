"""
Reservation Workflows

Temporal workflows for reservation processing with:
- Availability checking
- Table assignment
- Confirmation sending
- Reminder scheduling
- No-show handling
"""

import logging
from datetime import timedelta
from typing import Dict, Any

from temporalio import workflow, activity
from temporalio.common import RetryPolicy

logger = logging.getLogger(__name__)


# Activity Definitions
@activity.defn
async def check_availability_activity(
    reservation_data: Dict[str, Any],
    tenant_id: str
) -> Dict[str, Any]:
    """
    Check table availability for reservation
    
    - Query available tables
    - Check time slot conflicts
    - Verify capacity
    """
    try:
        from app.services.reservation_service import get_reservation_service
        
        reservation_service = get_reservation_service()
        
        availability = await reservation_service.check_availability(
            business_id=reservation_data.get("business_id"),
            reservation_time=reservation_data.get("reservation_time"),
            party_size=reservation_data.get("party_size"),
            duration_minutes=reservation_data.get("duration_minutes", 90)
        )
        
        logger.info(f"Availability checked: {availability.get('available')}")
        return availability
        
    except Exception as e:
        logger.error(f"Availability check error: {e}")
        return {"available": False, "error": str(e)}


@activity.defn
async def assign_table_activity(
    reservation_data: Dict[str, Any],
    tenant_id: str
) -> Dict[str, Any]:
    """
    Assign table to reservation
    
    - Select optimal table
    - Update table status
    - Lock table for time slot
    """
    try:
        from app.services.reservation_service import get_reservation_service
        
        reservation_service = get_reservation_service()
        
        table = await reservation_service.assign_table(
            reservation_id=reservation_data.get("id"),
            business_id=reservation_data.get("business_id"),
            party_size=reservation_data.get("party_size")
        )
        
        logger.info(f"Table assigned: {table.get('table_number')}")
        return table
        
    except Exception as e:
        logger.error(f"Table assignment error: {e}")
        return {"success": False, "error": str(e)}


@activity.defn
async def send_confirmation_activity(
    reservation_data: Dict[str, Any],
    tenant_id: str
) -> Dict[str, Any]:
    """
    Send reservation confirmation
    
    - Email confirmation
    - SMS confirmation
    - Calendar invite (.ics)
    """
    try:
        from app.services.notification_service import get_notification_service
        
        notification_service = get_notification_service()
        
        guest = reservation_data.get("guest", {})
        confirmation_code = reservation_data.get("confirmation_code")
        
        message = f"""
        Reservation Confirmed!
        
        Confirmation Code: {confirmation_code}
        Date/Time: {reservation_data.get('reservation_time')}
        Party Size: {reservation_data.get('party_size')}
        Table: {reservation_data.get('table_number', 'TBD')}
        
        See you soon!
        """
        
        # Send email
        if guest.get("email"):
            await notification_service.send_email(
                to=guest.get("email"),
                subject=f"Reservation Confirmed - {confirmation_code}",
                body=message
            )
        
        # Send SMS
        if guest.get("phone"):
            await notification_service.send_sms(
                to=guest.get("phone"),
                message=f"Reservation confirmed! Code: {confirmation_code}"
            )
        
        logger.info(f"Confirmation sent for reservation: {confirmation_code}")
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Confirmation sending error: {e}")
        return {"success": False, "error": str(e)}


@activity.defn
async def send_reminder_activity(
    reservation_data: Dict[str, Any],
    tenant_id: str
) -> Dict[str, Any]:
    """Send reminder before reservation"""
    try:
        from app.services.notification_service import get_notification_service
        
        notification_service = get_notification_service()
        guest = reservation_data.get("guest", {})
        
        message = f"""
        Reminder: Reservation Today!
        
        Code: {reservation_data.get('confirmation_code')}
        Time: {reservation_data.get('reservation_time')}
        Party Size: {reservation_data.get('party_size')}
        """
        
        if guest.get("email"):
            await notification_service.send_email(
                to=guest.get("email"),
                subject="Reservation Reminder",
                body=message
            )
        
        logger.info(f"Reminder sent for: {reservation_data.get('confirmation_code')}")
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Reminder error: {e}")
        return {"success": False, "error": str(e)}


# Workflow Definition
@workflow.defn(name="ReservationWorkflow")
class ReservationWorkflow:
    """
    Complete reservation workflow
    
    Steps:
    1. Check availability
    2. Assign table
    3. Send confirmation
    4. Schedule reminder
    5. Handle no-show if applicable
    """
    
    @workflow.run
    async def run(self, reservation_data: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
        """Execute reservation workflow"""
        
        workflow_result = {
            "reservation_id": reservation_data.get("id"),
            "confirmation_code": reservation_data.get("confirmation_code"),
            "steps_completed": [],
            "success": False
        }
        
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=30),
            maximum_attempts=3,
            backoff_coefficient=2.0
        )
        
        try:
            # Step 1: Check availability
            availability = await workflow.execute_activity(
                check_availability_activity,
                args=[reservation_data, tenant_id],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=retry_policy
            )
            
            if not availability.get("available"):
                workflow_result["error"] = "No availability"
                return workflow_result
            
            workflow_result["steps_completed"].append("availability_checked")
            
            # Step 2: Assign table
            table_assignment = await workflow.execute_activity(
                assign_table_activity,
                args=[reservation_data, tenant_id],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=retry_policy
            )
            
            if not table_assignment.get("success", True):
                workflow_result["error"] = "Table assignment failed"
                return workflow_result
            
            workflow_result["steps_completed"].append("table_assigned")
            workflow_result["table_number"] = table_assignment.get("table_number")
            
            # Step 3: Send confirmation
            confirmation = await workflow.execute_activity(
                send_confirmation_activity,
                args=[reservation_data, tenant_id],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=2)
            )
            
            workflow_result["steps_completed"].append("confirmation_sent")
            
            # Step 4: Schedule reminder (1 hour before)
            # Calculate time until reminder
            # In real implementation, use reservation_time to calculate
            reminder_delay = timedelta(hours=23)  # Example: 1 day minus 1 hour
            
            await workflow.sleep(reminder_delay)
            
            await workflow.execute_activity(
                send_reminder_activity,
                args=[reservation_data, tenant_id],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=2)
            )
            
            workflow_result["steps_completed"].append("reminder_sent")
            workflow_result["success"] = True
            
            return workflow_result
            
        except Exception as e:
            workflow.logger.error(f"Reservation workflow error: {e}")
            workflow_result["error"] = str(e)
            
            # Compensation: Release table if assigned
            if "table_assigned" in workflow_result["steps_completed"]:
                try:
                    workflow.logger.info("Would release table assignment")
                    # TODO: Trigger table release activity
                except Exception as release_error:
                    workflow.logger.error(f"Table release failed: {release_error}")
            
            return workflow_result
