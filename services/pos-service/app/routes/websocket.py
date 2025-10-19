"""
WebSocket Routes
Real-time order and table updates for mobile apps and dashboards
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Set, Dict
from uuid import UUID
import json
import asyncio
from datetime import datetime

from ..core.security import decode_token

router = APIRouter()


class ConnectionManager:
    """Manage WebSocket connections for real-time updates"""
    
    def __init__(self):
        # business_id -> Set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # connection -> business_id mapping
        self.connection_business_map: Dict[WebSocket, str] = {}
    
    async def connect(self, websocket: WebSocket, business_id: str):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        
        if business_id not in self.active_connections:
            self.active_connections[business_id] = set()
        
        self.active_connections[business_id].add(websocket)
        self.connection_business_map[websocket] = business_id
        
        # Send connection confirmation
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "business_id": business_id,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        business_id = self.connection_business_map.get(websocket)
        if business_id and business_id in self.active_connections:
            self.active_connections[business_id].discard(websocket)
            if not self.active_connections[business_id]:
                del self.active_connections[business_id]
        
        if websocket in self.connection_business_map:
            del self.connection_business_map[websocket]
    
    async def broadcast_to_business(self, business_id: str, message: dict):
        """Broadcast message to all connections for a business"""
        if business_id not in self.active_connections:
            return
        
        # Add timestamp to message
        message["timestamp"] = datetime.utcnow().isoformat()
        
        disconnected = set()
        for connection in self.active_connections[business_id]:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)
    
    async def send_to_connection(self, websocket: WebSocket, message: dict):
        """Send message to a specific connection"""
        try:
            message["timestamp"] = datetime.utcnow().isoformat()
            await websocket.send_json(message)
        except Exception:
            self.disconnect(websocket)


# Global connection manager
manager = ConnectionManager()


@router.websocket("/api/v1/pos/ws/orders")
async def websocket_orders(websocket: WebSocket, token: str = None):
    """
    WebSocket endpoint for real-time order updates
    
    Messages sent to clients:
    - order_created: New order created
    - order_updated: Order details updated
    - order_status_changed: Order status changed
    - order_cancelled: Order cancelled
    - order_completed: Order completed with payment
    
    Query params:
    - token: JWT authentication token
    """
    try:
        # Authenticate
        if not token:
            await websocket.close(code=1008, reason="Missing authentication token")
            return
        
        try:
            payload = decode_token(token)
            business_id = payload.get("business_id")
            if not business_id:
                await websocket.close(code=1008, reason="Invalid token: missing business_id")
                return
        except Exception as e:
            await websocket.close(code=1008, reason=f"Authentication failed: {str(e)}")
            return
        
        # Connect
        await manager.connect(websocket, business_id)
        
        try:
            # Keep connection alive and handle incoming messages
            while True:
                # Receive any messages from client (e.g., ping/pong)
                data = await websocket.receive_text()
                
                # Handle client messages
                try:
                    message = json.loads(data)
                    if message.get("type") == "ping":
                        await manager.send_to_connection(websocket, {
                            "type": "pong",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                except json.JSONDecodeError:
                    pass
                
        except WebSocketDisconnect:
            manager.disconnect(websocket)
            
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass


@router.websocket("/api/v1/pos/ws/tables")
async def websocket_tables(websocket: WebSocket, token: str = None):
    """
    WebSocket endpoint for real-time table status updates
    
    Messages sent to clients:
    - table_occupied: Table marked as occupied
    - table_available: Table marked as available
    - table_reserved: Table reserved
    - table_cleaning: Table being cleaned
    
    Query params:
    - token: JWT authentication token
    """
    try:
        # Authenticate
        if not token:
            await websocket.close(code=1008, reason="Missing authentication token")
            return
        
        try:
            payload = decode_token(token)
            business_id = payload.get("business_id")
            if not business_id:
                await websocket.close(code=1008, reason="Invalid token: missing business_id")
                return
        except Exception as e:
            await websocket.close(code=1008, reason=f"Authentication failed: {str(e)}")
            return
        
        # Connect
        await manager.connect(websocket, business_id)
        
        try:
            # Keep connection alive
            while True:
                data = await websocket.receive_text()
                
                # Handle ping/pong
                try:
                    message = json.loads(data)
                    if message.get("type") == "ping":
                        await manager.send_to_connection(websocket, {
                            "type": "pong",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                except json.JSONDecodeError:
                    pass
                
        except WebSocketDisconnect:
            manager.disconnect(websocket)
            
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass


# Helper functions to broadcast events
async def broadcast_order_event(business_id: str, event_type: str, order_data: dict):
    """Broadcast order-related event to all connected clients"""
    await manager.broadcast_to_business(business_id, {
        "type": event_type,
        "data": order_data
    })


async def broadcast_table_event(business_id: str, event_type: str, table_data: dict):
    """Broadcast table-related event to all connected clients"""
    await manager.broadcast_to_business(business_id, {
        "type": event_type,
        "data": table_data
    })


def get_connection_manager() -> ConnectionManager:
    """Get global connection manager instance"""
    return manager
