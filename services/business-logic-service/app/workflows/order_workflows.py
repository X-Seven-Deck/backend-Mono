"""
Order Fulfillment Workflows

Temporal workflows for order processing with:
- Order validation
- Payment processing
- Inventory management
- Kitchen/preparation tracking
- Customer notifications
- Compensation on failures
"""

import logging
from datetime import timedelta
from typing import Dict, Any

from temporalio import workflow, activity
from temporalio.common import RetryPolicy

logger = logging.getLogger(__name__)


# Activity Definitions
@activity.defn
async def validate_order_activity(order_data: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
    """
    Validate order details
    
    - Check menu items availability
    - Validate pricing
    - Verify business is accepting orders
    """
    try:
        from app.services.supabase_service import get_supabase_service
        
        db = get_supabase_service()
        business_id = order_data.get("business_id")
        
        # Get menu items
        menu_items = await db.get_menu_items(business_id)
        menu_item_ids = {item["id"] for item in menu_items}
        
        # Validate all items exist
        for item in order_data.get("items", []):
            menu_item_id = item.get("menu_item_id")
            if menu_item_id and menu_item_id not in menu_item_ids:
                return {
                    "valid": False,
                    "error": f"Menu item {menu_item_id} not found"
                }
        
        logger.info(f"Order validated for business {business_id}")
        return {"valid": True}
        
    except Exception as e:
        logger.error(f"Order validation error: {e}")
        return {"valid": False, "error": str(e)}


@activity.defn
async def process_payment_activity(order_data: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
    """
    Process payment for order
    
    - Create payment intent
    - Capture payment
    - Handle payment failures
    """
    try:
        from app.services.payment_service import get_payment_service
        
        payment_service = get_payment_service()
        
        # Process payment
        result = await payment_service.process_payment(
            amount=order_data.get("total_amount"),
            payment_method=order_data.get("payment_method", "card"),
            metadata={
                "order_id": order_data.get("id"),
                "order_number": order_data.get("order_number"),
                "tenant_id": tenant_id
            }
        )
        
        logger.info(f"Payment processed for order {order_data.get('order_number')}")
        return result
        
    except Exception as e:
        logger.error(f"Payment processing error: {e}")
        return {"success": False, "error": str(e)}


@activity.defn
async def prepare_order_activity(order_data: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
    """
    Send order to kitchen/preparation
    
    - Update order status to PREPARING
    - Send to kitchen display system
    - Track preparation progress
    """
    try:
        from app.services.order_service import get_order_service
        from app.models.orders import OrderStatus
        
        order_service = get_order_service()
        
        # Update order status
        await order_service._update_order_status(
            order_data.get("id"),
            OrderStatus.PREPARING
        )
        
        # TODO: Send to kitchen display system
        
        logger.info(f"Order sent to preparation: {order_data.get('order_number')}")
        return {"success": True, "status": "preparing"}
        
    except Exception as e:
        logger.error(f"Order preparation error: {e}")
        return {"success": False, "error": str(e)}


@activity.defn
async def notify_customer_activity(
    order_data: Dict[str, Any],
    notification_type: str,
    tenant_id: str
) -> Dict[str, Any]:
    """
    Send customer notification
    
    - Order confirmation
    - Status updates
    - Ready for pickup/delivery
    """
    try:
        from app.services.notification_service import get_notification_service
        
        notification_service = get_notification_service()
        
        customer = order_data.get("customer", {})
        email = customer.get("email")
        phone = customer.get("phone")
        
        if notification_type == "confirmation":
            message = f"Order {order_data.get('order_number')} confirmed!"
        elif notification_type == "ready":
            message = f"Your order is ready for pickup!"
        elif notification_type == "completed":
            message = f"Order delivered. Thank you!"
        else:
            message = f"Order status: {notification_type}"
        
        # Send notification
        if email:
            await notification_service.send_email(
                to=email,
                subject=f"Order Update: {order_data.get('order_number')}",
                body=message
            )
        
        if phone:
            await notification_service.send_sms(
                to=phone,
                message=message
            )
        
        logger.info(f"Customer notified: {notification_type}")
        return {"success": True, "notification_type": notification_type}
        
    except Exception as e:
        logger.error(f"Customer notification error: {e}")
        return {"success": False, "error": str(e)}


@activity.defn
async def update_inventory_activity(order_data: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
    """Deduct inventory for completed order"""
    try:
        from app.services.inventory_service import get_inventory_service
        
        inventory_service = get_inventory_service()
        
        # Deduct inventory for each item
        for item in order_data.get("items", []):
            if item.get("menu_item_id"):
                # TODO: Map menu items to inventory items
                logger.info(f"Would deduct inventory for: {item.get('name')}")
        
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Inventory update error: {e}")
        return {"success": False, "error": str(e)}


# Workflow Definition
@workflow.defn(name="OrderFulfillmentWorkflow")
class OrderFulfillmentWorkflow:
    """
    Complete order fulfillment workflow
    
    Steps:
    1. Validate order
    2. Process payment
    3. Send to kitchen/preparation
    4. Notify customer
    5. Update inventory
    6. Mark as completed
    
    Handles compensation on failures
    """
    
    @workflow.run
    async def run(self, order_data: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
        """Execute order fulfillment workflow"""
        
        workflow_result = {
            "order_id": order_data.get("id"),
            "order_number": order_data.get("order_number"),
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
            # Step 1: Validate order
            validation_result = await workflow.execute_activity(
                validate_order_activity,
                args=[order_data, tenant_id],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=retry_policy
            )
            
            if not validation_result.get("valid"):
                workflow_result["error"] = validation_result.get("error")
                return workflow_result
            
            workflow_result["steps_completed"].append("validated")
            
            # Step 2: Process payment
            payment_result = await workflow.execute_activity(
                process_payment_activity,
                args=[order_data, tenant_id],
                start_to_close_timeout=timedelta(seconds=60),
                retry_policy=retry_policy
            )
            
            if not payment_result.get("success"):
                workflow_result["error"] = "Payment failed"
                return workflow_result
            
            workflow_result["steps_completed"].append("payment_processed")
            workflow_result["payment_id"] = payment_result.get("transaction_id")
            
            # Step 3: Send to kitchen/preparation
            preparation_result = await workflow.execute_activity(
                prepare_order_activity,
                args=[order_data, tenant_id],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=retry_policy
            )
            
            workflow_result["steps_completed"].append("preparing")
            
            # Step 4: Notify customer (confirmation)
            await workflow.execute_activity(
                notify_customer_activity,
                args=[order_data, "confirmation", tenant_id],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=2)  # Non-critical
            )
            
            workflow_result["steps_completed"].append("customer_notified")
            
            # Step 5: Wait for preparation completion (simulated)
            # In real implementation, this would wait for kitchen signal
            await workflow.sleep(timedelta(seconds=10))
            
            # Step 6: Update inventory
            await workflow.execute_activity(
                update_inventory_activity,
                args=[order_data, tenant_id],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=retry_policy
            )
            
            workflow_result["steps_completed"].append("inventory_updated")
            
            # Step 7: Final notification
            await workflow.execute_activity(
                notify_customer_activity,
                args=[order_data, "completed", tenant_id],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=2)
            )
            
            workflow_result["success"] = True
            workflow_result["steps_completed"].append("completed")
            
            return workflow_result
            
        except Exception as e:
            workflow.logger.error(f"Order workflow error: {e}")
            workflow_result["error"] = str(e)
            
            # Compensation: Refund payment if processed
            if "payment_processed" in workflow_result["steps_completed"]:
                try:
                    # TODO: Trigger refund activity
                    workflow.logger.info("Would trigger payment refund")
                except Exception as refund_error:
                    workflow.logger.error(f"Refund failed: {refund_error}")
            
            return workflow_result
