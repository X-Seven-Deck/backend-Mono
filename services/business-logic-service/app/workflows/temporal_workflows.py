"""
Temporal Workflow Definitions

Production-grade durable workflows for business operations.
"""

from datetime import timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from temporalio import workflow, activity
from temporalio.common import RetryPolicy

import logging

logger = logging.getLogger(__name__)


# Data classes for workflow inputs/outputs
@dataclass
class OrderInput:
    """Order workflow input"""
    order_id: str
    business_id: str
    customer_id: str
    items: List[Dict[str, Any]]
    total_amount: float
    payment_method: str
    delivery_address: Optional[str] = None


@dataclass
class ReservationInput:
    """Reservation workflow input"""
    reservation_id: str
    business_id: str
    customer_id: str
    date: str
    time: str
    party_size: int
    special_requests: Optional[str] = None


@dataclass
class PaymentInput:
    """Payment workflow input"""
    transaction_id: str
    amount: float
    payment_method: str
    customer_id: str
    business_id: str


# Activities (actual business logic)
@activity.defn
async def validate_order_items(order_input: OrderInput) -> Dict[str, Any]:
    """Validate order items against business menu"""
    logger.info(f"Validating order items for order {order_input.order_id}")
    
    # TODO: Query Supabase for menu items and validate
    # Check if items exist, are available, and prices match
    
    return {
        "valid": True,
        "items_validated": len(order_input.items),
        "total_validated": order_input.total_amount
    }


@activity.defn
async def check_inventory(order_input: OrderInput) -> Dict[str, Any]:
    """Check inventory availability"""
    logger.info(f"Checking inventory for order {order_input.order_id}")
    
    # TODO: Query inventory database
    # Check if all items are in stock
    
    return {
        "available": True,
        "items_in_stock": len(order_input.items)
    }


@activity.defn
async def process_payment(payment_input: PaymentInput) -> Dict[str, Any]:
    """Process payment transaction"""
    logger.info(f"Processing payment {payment_input.transaction_id}")
    
    # TODO: Integrate with payment gateway (Stripe, Square, etc.)
    # Process payment and return transaction details
    
    return {
        "success": True,
        "transaction_id": payment_input.transaction_id,
        "amount_charged": payment_input.amount,
        "status": "completed"
    }


@activity.defn
async def create_order_record(order_input: OrderInput) -> Dict[str, Any]:
    """Create order record in database"""
    logger.info(f"Creating order record {order_input.order_id}")
    
    # TODO: Insert into Supabase orders table
    
    return {
        "order_id": order_input.order_id,
        "status": "confirmed",
        "created_at": "2025-10-04T15:00:00Z"
    }


@activity.defn
async def update_inventory(order_input: OrderInput) -> Dict[str, Any]:
    """Update inventory after order"""
    logger.info(f"Updating inventory for order {order_input.order_id}")
    
    # TODO: Decrement inventory counts in database
    
    return {
        "updated": True,
        "items_updated": len(order_input.items)
    }


@activity.defn
async def send_order_confirmation(order_input: OrderInput) -> Dict[str, Any]:
    """Send order confirmation to customer"""
    logger.info(f"Sending confirmation for order {order_input.order_id}")
    
    # TODO: Send email/SMS via notification service
    
    return {
        "sent": True,
        "customer_id": order_input.customer_id,
        "notification_type": "email"
    }


@activity.defn
async def notify_business(order_input: OrderInput) -> Dict[str, Any]:
    """Notify business of new order"""
    logger.info(f"Notifying business for order {order_input.order_id}")
    
    # TODO: Send notification to business dashboard/app
    
    return {
        "notified": True,
        "business_id": order_input.business_id
    }


@activity.defn
async def check_reservation_availability(reservation_input: ReservationInput) -> Dict[str, Any]:
    """Check if reservation slot is available"""
    logger.info(f"Checking availability for reservation {reservation_input.reservation_id}")
    
    # TODO: Query reservations table for conflicts
    
    return {
        "available": True,
        "slot": f"{reservation_input.date} {reservation_input.time}"
    }


@activity.defn
async def create_reservation_record(reservation_input: ReservationInput) -> Dict[str, Any]:
    """Create reservation record in database"""
    logger.info(f"Creating reservation {reservation_input.reservation_id}")
    
    # TODO: Insert into Supabase reservations table
    
    return {
        "reservation_id": reservation_input.reservation_id,
        "status": "confirmed",
        "confirmation_code": f"CONF{reservation_input.reservation_id[-6:].upper()}"
    }


@activity.defn
async def send_reservation_confirmation(reservation_input: ReservationInput) -> Dict[str, Any]:
    """Send reservation confirmation"""
    logger.info(f"Sending confirmation for reservation {reservation_input.reservation_id}")
    
    # TODO: Send confirmation email/SMS
    
    return {
        "sent": True,
        "customer_id": reservation_input.customer_id
    }


@activity.defn
async def add_to_calendar(reservation_input: ReservationInput) -> Dict[str, Any]:
    """Add reservation to customer's calendar"""
    logger.info(f"Adding to calendar: {reservation_input.reservation_id}")
    
    # TODO: Generate calendar invite (iCal format)
    
    return {
        "calendar_invite_sent": True
    }


# Workflows
@workflow.defn
class OrderFulfillmentWorkflow:
    """
    Complete order fulfillment workflow
    
    Steps:
    1. Validate order items
    2. Check inventory
    3. Process payment
    4. Create order record
    5. Update inventory
    6. Send confirmations
    """
    
    @workflow.run
    async def run(self, order_input: OrderInput) -> Dict[str, Any]:
        """Execute order fulfillment workflow"""
        
        workflow.logger.info(f"Starting order fulfillment for {order_input.order_id}")
        
        # Define retry policy
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=30),
            maximum_attempts=3
        )
        
        try:
            # Step 1: Validate order items
            validation_result = await workflow.execute_activity(
                validate_order_items,
                order_input,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=retry_policy
            )
            
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": "Order validation failed",
                    "order_id": order_input.order_id
                }
            
            # Step 2: Check inventory
            inventory_result = await workflow.execute_activity(
                check_inventory,
                order_input,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=retry_policy
            )
            
            if not inventory_result["available"]:
                return {
                    "success": False,
                    "error": "Items not available",
                    "order_id": order_input.order_id
                }
            
            # Step 3: Process payment
            payment_input = PaymentInput(
                transaction_id=f"txn_{order_input.order_id}",
                amount=order_input.total_amount,
                payment_method=order_input.payment_method,
                customer_id=order_input.customer_id,
                business_id=order_input.business_id
            )
            
            payment_result = await workflow.execute_activity(
                process_payment,
                payment_input,
                start_to_close_timeout=timedelta(seconds=60),
                retry_policy=retry_policy
            )
            
            if not payment_result["success"]:
                return {
                    "success": False,
                    "error": "Payment failed",
                    "order_id": order_input.order_id
                }
            
            # Step 4: Create order record
            order_record = await workflow.execute_activity(
                create_order_record,
                order_input,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=retry_policy
            )
            
            # Step 5: Update inventory
            await workflow.execute_activity(
                update_inventory,
                order_input,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=retry_policy
            )
            
            # Step 6: Send confirmations (parallel)
            confirmation_tasks = [
                workflow.execute_activity(
                    send_order_confirmation,
                    order_input,
                    start_to_close_timeout=timedelta(seconds=30)
                ),
                workflow.execute_activity(
                    notify_business,
                    order_input,
                    start_to_close_timeout=timedelta(seconds=30)
                )
            ]
            
            await workflow.wait(confirmation_tasks)
            
            workflow.logger.info(f"Order fulfillment complete for {order_input.order_id}")
            
            return {
                "success": True,
                "order_id": order_input.order_id,
                "status": "confirmed",
                "payment_status": payment_result["status"],
                "transaction_id": payment_result["transaction_id"]
            }
            
        except Exception as e:
            workflow.logger.error(f"Order fulfillment failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "order_id": order_input.order_id
            }


@workflow.defn
class ReservationWorkflow:
    """
    Complete reservation workflow
    
    Steps:
    1. Check availability
    2. Create reservation
    3. Send confirmation
    4. Add to calendar
    """
    
    @workflow.run
    async def run(self, reservation_input: ReservationInput) -> Dict[str, Any]:
        """Execute reservation workflow"""
        
        workflow.logger.info(f"Starting reservation for {reservation_input.reservation_id}")
        
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=30),
            maximum_attempts=3
        )
        
        try:
            # Step 1: Check availability
            availability_result = await workflow.execute_activity(
                check_reservation_availability,
                reservation_input,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=retry_policy
            )
            
            if not availability_result["available"]:
                return {
                    "success": False,
                    "error": "Time slot not available",
                    "reservation_id": reservation_input.reservation_id
                }
            
            # Step 2: Create reservation record
            reservation_record = await workflow.execute_activity(
                create_reservation_record,
                reservation_input,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=retry_policy
            )
            
            # Step 3 & 4: Send confirmation and calendar invite (parallel)
            notification_tasks = [
                workflow.execute_activity(
                    send_reservation_confirmation,
                    reservation_input,
                    start_to_close_timeout=timedelta(seconds=30)
                ),
                workflow.execute_activity(
                    add_to_calendar,
                    reservation_input,
                    start_to_close_timeout=timedelta(seconds=30)
                )
            ]
            
            await workflow.wait(notification_tasks)
            
            workflow.logger.info(f"Reservation complete for {reservation_input.reservation_id}")
            
            return {
                "success": True,
                "reservation_id": reservation_input.reservation_id,
                "status": "confirmed",
                "confirmation_code": reservation_record["confirmation_code"]
            }
            
        except Exception as e:
            workflow.logger.error(f"Reservation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "reservation_id": reservation_input.reservation_id
            }


@workflow.defn
class PaymentProcessingWorkflow:
    """
    Standalone payment processing workflow
    
    Can be used for refunds, partial payments, etc.
    """
    
    @workflow.run
    async def run(self, payment_input: PaymentInput) -> Dict[str, Any]:
        """Execute payment workflow"""
        
        workflow.logger.info(f"Processing payment {payment_input.transaction_id}")
        
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=60),
            maximum_attempts=5
        )
        
        try:
            result = await workflow.execute_activity(
                process_payment,
                payment_input,
                start_to_close_timeout=timedelta(seconds=120),
                retry_policy=retry_policy
            )
            
            return result
            
        except Exception as e:
            workflow.logger.error(f"Payment processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "transaction_id": payment_input.transaction_id
            }
