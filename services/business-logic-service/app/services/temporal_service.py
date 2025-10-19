"""
Temporal Workflow Orchestration Service

Complete Temporal integration for durable workflow execution with:
- Client initialization and management
- Worker setup and lifecycle
- Workflow execution from API endpoints
- Activity implementation with retry logic
- Error handling and compensation
- Integration with business services
"""

import logging
import asyncio
from typing import Optional, Dict, Any, List
from datetime import timedelta
from dataclasses import dataclass

from temporalio import workflow, activity
from temporalio.client import Client, WorkflowHandle
from temporalio.worker import Worker
from temporalio.common import RetryPolicy

from app.config.settings import get_settings
from app.models.orders import Order, OrderStatus
from app.models.reservations import Reservation, ReservationStatus

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class WorkflowConfig:
    """Workflow configuration"""
    task_queue: str = settings.TEMPORAL_TASK_QUEUE
    workflow_id_prefix: str = "business-logic"
    execution_timeout: timedelta = timedelta(hours=24)
    task_timeout: timedelta = timedelta(minutes=5)
    retry_policy: RetryPolicy = RetryPolicy(
        initial_interval=timedelta(seconds=1),
        maximum_interval=timedelta(seconds=60),
        maximum_attempts=3,
        backoff_coefficient=2.0
    )


class TemporalService:
    """
    Complete Temporal orchestration service
    
    Features:
    - Workflow client management
    - Worker lifecycle management
    - Order fulfillment workflows
    - Reservation workflows
    - Payment processing workflows
    - Inventory management workflows
    - Compensation logic for failures
    """
    
    def __init__(self):
        self.client: Optional[Client] = None
        self.worker: Optional[Worker] = None
        self.config = WorkflowConfig()
        self.running = False
    
    async def start(self):
        """Initialize Temporal client and worker"""
        try:
            # Connect to Temporal server
            self.client = await Client.connect(
                settings.temporal_url,
                namespace=settings.TEMPORAL_NAMESPACE
            )
            logger.info(f"✅ Connected to Temporal server at {settings.temporal_url}")
            
            # Start worker
            await self._start_worker()
            
            self.running = True
            logger.info("✅ Temporal service started successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to start Temporal service: {e}", exc_info=True)
            raise
    
    async def stop(self):
        """Shutdown Temporal connections"""
        self.running = False
        
        if self.worker:
            await self.worker.shutdown()
            logger.info("Temporal worker stopped")
        
        if self.client:
            # Client doesn't need explicit shutdown
            logger.info("Temporal client disconnected")
    
    async def _start_worker(self):
        """Start Temporal worker"""
        try:
            # Import workflows and activities
            from app.workflows.order_workflows import (
                OrderFulfillmentWorkflow,
                validate_order_activity,
                process_payment_activity,
                prepare_order_activity,
                notify_customer_activity
            )
            from app.workflows.reservation_workflows import (
                ReservationWorkflow,
                check_availability_activity,
                assign_table_activity,
                send_confirmation_activity
            )
            
            self.worker = Worker(
                self.client,
                task_queue=self.config.task_queue,
                workflows=[
                    OrderFulfillmentWorkflow,
                    ReservationWorkflow
                ],
                activities=[
                    validate_order_activity,
                    process_payment_activity,
                    prepare_order_activity,
                    notify_customer_activity,
                    check_availability_activity,
                    assign_table_activity,
                    send_confirmation_activity
                ],
                max_concurrent_workflow_tasks=100,
                max_concurrent_activities=50
            )
            
            # Run worker in background
            asyncio.create_task(self.worker.run())
            logger.info(f"Temporal worker started on task queue: {self.config.task_queue}")
            
        except Exception as e:
            logger.error(f"Error starting worker: {e}", exc_info=True)
            raise
    
    async def execute_order_workflow(
        self,
        order: Order,
        tenant_id: str
    ) -> WorkflowHandle:
        """
        Execute order fulfillment workflow
        
        Args:
            order: Order object
            tenant_id: Tenant identifier
        
        Returns:
            WorkflowHandle for tracking execution
        """
        try:
            if not self.client:
                raise RuntimeError("Temporal client not initialized")
            
            workflow_id = f"{self.config.workflow_id_prefix}-order-{order.order_number}"
            
            # Start workflow
            handle = await self.client.start_workflow(
                "OrderFulfillmentWorkflow",
                args=[order.dict(), tenant_id],
                id=workflow_id,
                task_queue=self.config.task_queue,
                execution_timeout=self.config.execution_timeout,
                retry_policy=self.config.retry_policy
            )
            
            logger.info(
                f"Started order workflow: {workflow_id}",
                extra={"order_id": order.id, "tenant_id": tenant_id}
            )
            
            return handle
            
        except Exception as e:
            logger.error(f"Error executing order workflow: {e}", exc_info=True)
            raise
    
    async def execute_reservation_workflow(
        self,
        reservation: Reservation,
        tenant_id: str
    ) -> WorkflowHandle:
        """
        Execute reservation workflow
        
        Args:
            reservation: Reservation object
            tenant_id: Tenant identifier
        
        Returns:
            WorkflowHandle for tracking execution
        """
        try:
            if not self.client:
                raise RuntimeError("Temporal client not initialized")
            
            workflow_id = f"{self.config.workflow_id_prefix}-reservation-{reservation.confirmation_code}"
            
            # Start workflow
            handle = await self.client.start_workflow(
                "ReservationWorkflow",
                args=[reservation.dict(), tenant_id],
                id=workflow_id,
                task_queue=self.config.task_queue,
                execution_timeout=self.config.execution_timeout,
                retry_policy=self.config.retry_policy
            )
            
            logger.info(
                f"Started reservation workflow: {workflow_id}",
                extra={"reservation_id": reservation.id, "tenant_id": tenant_id}
            )
            
            return handle
            
        except Exception as e:
            logger.error(f"Error executing reservation workflow: {e}", exc_info=True)
            raise
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get workflow execution status
        
        Args:
            workflow_id: Workflow identifier
        
        Returns:
            Dict with workflow status information
        """
        try:
            if not self.client:
                raise RuntimeError("Temporal client not initialized")
            
            handle = self.client.get_workflow_handle(workflow_id)
            
            # Get workflow info
            description = await handle.describe()
            
            return {
                "workflow_id": workflow_id,
                "status": description.status.name,
                "start_time": description.start_time,
                "execution_time": description.execution_time,
                "close_time": description.close_time,
                "is_running": description.status.name in ["RUNNING", "CONTINUED_AS_NEW"]
            }
            
        except Exception as e:
            logger.error(f"Error getting workflow status: {e}")
            return {
                "workflow_id": workflow_id,
                "status": "UNKNOWN",
                "error": str(e)
            }
    
    async def cancel_workflow(self, workflow_id: str, reason: str = ""):
        """
        Cancel a running workflow
        
        Args:
            workflow_id: Workflow identifier
            reason: Cancellation reason
        """
        try:
            if not self.client:
                raise RuntimeError("Temporal client not initialized")
            
            handle = self.client.get_workflow_handle(workflow_id)
            await handle.cancel()
            
            logger.info(f"Cancelled workflow: {workflow_id}, reason: {reason}")
            
        except Exception as e:
            logger.error(f"Error cancelling workflow: {e}")
            raise
    
    async def signal_workflow(
        self,
        workflow_id: str,
        signal_name: str,
        signal_args: List[Any]
    ):
        """
        Send signal to running workflow
        
        Args:
            workflow_id: Workflow identifier
            signal_name: Signal name
            signal_args: Signal arguments
        """
        try:
            if not self.client:
                raise RuntimeError("Temporal client not initialized")
            
            handle = self.client.get_workflow_handle(workflow_id)
            await handle.signal(signal_name, *signal_args)
            
            logger.info(f"Sent signal {signal_name} to workflow {workflow_id}")
            
        except Exception as e:
            logger.error(f"Error signaling workflow: {e}")
            raise


# Singleton instance
_temporal_service: Optional[TemporalService] = None


def get_temporal_service() -> TemporalService:
    """Get Temporal service singleton"""
    global _temporal_service
    if _temporal_service is None:
        _temporal_service = TemporalService()
    return _temporal_service
