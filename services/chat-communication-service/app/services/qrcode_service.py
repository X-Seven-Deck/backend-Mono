"""
QR Code Generation Service

Dynamic QR codes for context-aware chat initialization.
"""

import os
from typing import Dict, Optional, Any
import logging
import qrcode
from io import BytesIO
import base64
import hashlib
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class QRCodeService:
    """
    QR Code Generation and Management Service
    
    Features:
    - Dynamic QR code generation
    - Context embedding (business, table, product, etc.)
    - Shareable link management
    - Analytics tracking
    - Expiration management
    """
    
    def __init__(self):
        self.base_url = os.getenv("CHAT_BASE_URL", "https://chat.x7ai.com")
        self._qr_codes: Dict[str, Dict] = {}  # In-memory storage (future: Redis)
    
    def generate_qr_code(
        self,
        business_id: str,
        context_type: str,  # table, product, service, general
        context_data: Dict[str, Any],
        expires_in_hours: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate dynamic QR code with embedded context.
        
        Args:
            business_id: Business identifier
            context_type: Type of context (table, product, service, general)
            context_data: Context-specific data
            expires_in_hours: Optional expiration time
        
        Returns:
            QR code image (base64), shareable link, and metadata
        """
        try:
            # Generate unique QR code ID
            qr_id = self._generate_qr_id(business_id, context_type, context_data)
            
            # Build chat URL with embedded context
            chat_url = self._build_chat_url(qr_id, business_id, context_type, context_data)
            
            # Generate QR code image
            qr_image = self._create_qr_image(chat_url)
            
            # Calculate expiration
            expires_at = None
            if expires_in_hours:
                expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
            
            # Store QR code metadata
            qr_metadata = {
                "qr_id": qr_id,
                "business_id": business_id,
                "context_type": context_type,
                "context_data": context_data,
                "chat_url": chat_url,
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": expires_at.isoformat() if expires_at else None,
                "scan_count": 0,
                "active": True
            }
            
            self._qr_codes[qr_id] = qr_metadata
            
            logger.info(
                f"Generated QR code {qr_id} for business {business_id}, "
                f"type: {context_type}"
            )
            
            return {
                "qr_id": qr_id,
                "qr_image_base64": qr_image,
                "chat_url": chat_url,
                "shareable_link": chat_url,
                "context_type": context_type,
                "expires_at": expires_at.isoformat() if expires_at else None,
                "metadata": qr_metadata
            }
            
        except Exception as e:
            logger.error(f"Error generating QR code: {e}")
            raise
    
    def generate_table_qr(
        self,
        business_id: str,
        table_number: str,
        table_name: Optional[str] = None,
        section: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate QR code for restaurant table.
        
        When scanned, initializes chat with table context.
        """
        context_data = {
            "table_number": table_number,
            "table_name": table_name or f"Table {table_number}",
            "section": section,
            "auto_message": f"Welcome! You're at {table_name or f'Table {table_number}'}. How can we help you today?"
        }
        
        return self.generate_qr_code(
            business_id=business_id,
            context_type="table",
            context_data=context_data
        )
    
    def generate_product_qr(
        self,
        business_id: str,
        product_id: str,
        product_name: str,
        product_image: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate QR code for product inquiry.
        
        When scanned, opens chat with product context.
        """
        context_data = {
            "product_id": product_id,
            "product_name": product_name,
            "product_image": product_image,
            "auto_message": f"I'm interested in {product_name}. Can you provide more information?"
        }
        
        return self.generate_qr_code(
            business_id=business_id,
            context_type="product",
            context_data=context_data
        )
    
    def generate_service_qr(
        self,
        business_id: str,
        service_id: str,
        service_name: str,
        service_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate QR code for service booking.
        
        When scanned, opens chat for service inquiry/booking.
        """
        context_data = {
            "service_id": service_id,
            "service_name": service_name,
            "service_type": service_type,
            "auto_message": f"I'd like to book {service_name}. What are the available times?"
        }
        
        return self.generate_qr_code(
            business_id=business_id,
            context_type="service",
            context_data=context_data
        )
    
    def generate_general_qr(
        self,
        business_id: str,
        welcome_message: Optional[str] = None,
        campaign_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate general business QR code.
        
        For marketing, storefronts, business cards, etc.
        """
        context_data = {
            "welcome_message": welcome_message or "Welcome! How can we help you today?",
            "campaign_id": campaign_id
        }
        
        return self.generate_qr_code(
            business_id=business_id,
            context_type="general",
            context_data=context_data,
            expires_in_hours=None  # No expiration for general QR
        )
    
    async def track_scan(self, qr_id: str, scan_metadata: Optional[Dict] = None) -> bool:
        """
        Track QR code scan with metadata.
        
        Args:
            qr_id: QR code identifier
            scan_metadata: Optional metadata (location, device, etc.)
        """
        try:
            if qr_id not in self._qr_codes:
                logger.warning(f"QR code {qr_id} not found")
                return False
            
            qr_data = self._qr_codes[qr_id]
            
            # Check expiration
            if qr_data.get("expires_at"):
                expires_at = datetime.fromisoformat(qr_data["expires_at"])
                if datetime.utcnow() > expires_at:
                    logger.warning(f"QR code {qr_id} has expired")
                    qr_data["active"] = False
                    return False
            
            # Increment scan count
            qr_data["scan_count"] += 1
            qr_data["last_scanned_at"] = datetime.utcnow().isoformat()
            
            if scan_metadata:
                if "scan_history" not in qr_data:
                    qr_data["scan_history"] = []
                
                qr_data["scan_history"].append({
                    "timestamp": datetime.utcnow().isoformat(),
                    **scan_metadata
                })
            
            logger.info(f"QR code {qr_id} scanned, total scans: {qr_data['scan_count']}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error tracking scan: {e}")
            return False
    
    def get_qr_context(self, qr_id: str) -> Optional[Dict]:
        """
        Get context data for QR code.
        
        Used when initializing chat from QR scan.
        """
        if qr_id not in self._qr_codes:
            return None
        
        qr_data = self._qr_codes[qr_id]
        
        # Check if active and not expired
        if not qr_data.get("active"):
            return None
        
        if qr_data.get("expires_at"):
            expires_at = datetime.fromisoformat(qr_data["expires_at"])
            if datetime.utcnow() > expires_at:
                return None
        
        return {
            "business_id": qr_data["business_id"],
            "context_type": qr_data["context_type"],
            "context_data": qr_data["context_data"]
        }
    
    def get_qr_analytics(self, qr_id: str) -> Optional[Dict]:
        """
        Get analytics for QR code.
        """
        if qr_id not in self._qr_codes:
            return None
        
        qr_data = self._qr_codes[qr_id]
        
        return {
            "qr_id": qr_id,
            "business_id": qr_data["business_id"],
            "context_type": qr_data["context_type"],
            "scan_count": qr_data["scan_count"],
            "created_at": qr_data["created_at"],
            "last_scanned_at": qr_data.get("last_scanned_at"),
            "expires_at": qr_data.get("expires_at"),
            "active": qr_data["active"],
            "scan_history": qr_data.get("scan_history", [])
        }
    
    def deactivate_qr(self, qr_id: str) -> bool:
        """Deactivate QR code"""
        if qr_id in self._qr_codes:
            self._qr_codes[qr_id]["active"] = False
            logger.info(f"QR code {qr_id} deactivated")
            return True
        return False
    
    def _generate_qr_id(
        self,
        business_id: str,
        context_type: str,
        context_data: Dict
    ) -> str:
        """Generate unique QR code ID"""
        data_str = f"{business_id}:{context_type}:{json.dumps(context_data, sort_keys=True)}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]
    
    def _build_chat_url(
        self,
        qr_id: str,
        business_id: str,
        context_type: str,
        context_data: Dict
    ) -> str:
        """Build chat URL with embedded context"""
        # Encode context data
        context_encoded = base64.urlsafe_b64encode(
            json.dumps(context_data).encode()
        ).decode()
        
        return (
            f"{self.base_url}/chat?"
            f"qr={qr_id}&"
            f"business={business_id}&"
            f"type={context_type}&"
            f"ctx={context_encoded}"
        )
    
    def _create_qr_image(self, data: str) -> str:
        """Create QR code image and return as base64"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return img_base64


# Singleton instance
_qrcode_service = None

def get_qrcode_service() -> QRCodeService:
    """Get singleton instance of QRCodeService"""
    global _qrcode_service
    if _qrcode_service is None:
        _qrcode_service = QRCodeService()
    return _qrcode_service
