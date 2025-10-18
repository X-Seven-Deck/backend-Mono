"""
Receipt Generation Service
Generate digital receipts in multiple formats
"""

from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from decimal import Decimal
import json

from ..core.config import settings
from ..models.receipts import ReceiptData, ReceiptLineItem
from .database import DatabaseService, get_database_service


class ReceiptGenerator:
    """Receipt generation service"""
    
    def __init__(self, db_service: DatabaseService):
        self.db = db_service
    
    async def generate_receipt(
        self,
        order_id: UUID,
        business_id: UUID,
        generated_by: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Generate receipt for order"""
        # Get order with items
        order = await self.db.get_order_with_items(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        # Get payment info
        payment = await self.db.get_payment_by_order(order_id)
        
        # Generate receipt number
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        receipt_number = f"{settings.RECEIPT_PREFIX}-{timestamp}"
        
        # Build line items
        line_items = []
        for item in order.get("items", []):
            modifiers = []
            if item.get("modifiers"):
                for mod in item["modifiers"]:
                    if isinstance(mod, dict):
                        modifiers.append(mod.get("name", str(mod)))
                    else:
                        modifiers.append(str(mod))
            
            line_items.append(ReceiptLineItem(
                name=item["name"],
                quantity=item["quantity"],
                unit_price=Decimal(str(item["unit_price"])),
                total=Decimal(str(item["quantity"])) * Decimal(str(item["unit_price"])),
                modifiers=modifiers
            ))
        
        # Calculate tax rate
        tax_rate = 0.0
        if order.get("subtotal") and Decimal(str(order["subtotal"])) > 0:
            tax_rate = float(
                Decimal(str(order.get("tax_amount", 0))) / Decimal(str(order["subtotal"]))
            )
        
        # Build receipt data
        receipt_data = ReceiptData(
            receipt_number=receipt_number,
            order_number=order.get("order_number"),
            business_name=settings.BUSINESS_NAME,
            business_address=settings.BUSINESS_ADDRESS,
            business_phone=settings.BUSINESS_PHONE,
            date=datetime.utcnow(),
            table_number=order.get("table_number"),
            server_name=None,  # TODO: Get from staff_id
            customer_count=order.get("customer_count", 1),
            items=line_items,
            subtotal=Decimal(str(order.get("subtotal", 0))),
            tax_amount=Decimal(str(order.get("tax_amount", 0))),
            tax_rate=tax_rate,
            discount_amount=Decimal(str(order.get("discount_amount", 0))),
            tip_amount=Decimal(str(payment.get("tip_amount", 0))) if payment else Decimal("0"),
            total_amount=Decimal(str(order.get("total_amount", 0))),
            payment_method=payment.get("payment_method", "unknown") if payment else "pending"
        )
        
        # Save receipt to database
        receipt_record = {
            "order_id": str(order_id),
            "receipt_number": receipt_number,
            "receipt_data": json.loads(receipt_data.model_dump_json()),
            "generated_by": str(generated_by) if generated_by else None
        }
        
        saved_receipt = await self.db.create_receipt(receipt_record)
        
        return {
            "id": saved_receipt["id"],
            "receipt_number": receipt_number,
            "receipt_data": receipt_data,
            "generated_at": saved_receipt["generated_at"]
        }
    
    def generate_receipt_html(self, receipt_data: ReceiptData) -> str:
        """Generate HTML receipt"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Receipt {receipt_data.receipt_number}</title>
            <style>
                body {{
                    font-family: 'Courier New', monospace;
                    max-width: 300px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 20px;
                }}
                .business-name {{
                    font-size: 18px;
                    font-weight: bold;
                }}
                .line-item {{
                    display: flex;
                    justify-content: space-between;
                    margin: 5px 0;
                }}
                .modifier {{
                    font-size: 12px;
                    color: #666;
                    margin-left: 20px;
                }}
                .totals {{
                    border-top: 1px dashed #000;
                    margin-top: 10px;
                    padding-top: 10px;
                }}
                .total-line {{
                    display: flex;
                    justify-content: space-between;
                    margin: 3px 0;
                }}
                .grand-total {{
                    font-weight: bold;
                    font-size: 16px;
                    border-top: 2px solid #000;
                    padding-top: 5px;
                    margin-top: 5px;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 20px;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="business-name">{receipt_data.business_name}</div>
                <div>{receipt_data.business_address}</div>
                <div>{receipt_data.business_phone}</div>
                <div style="margin-top: 10px;">
                    Receipt: {receipt_data.receipt_number}<br>
                    Date: {receipt_data.date.strftime('%Y-%m-%d %H:%M:%S')}
                </div>
                {f'<div>Table: {receipt_data.table_number}</div>' if receipt_data.table_number else ''}
                <div>Guests: {receipt_data.customer_count}</div>
            </div>
            
            <div class="items">
        """
        
        for item in receipt_data.items:
            html += f"""
                <div class="line-item">
                    <span>{item.quantity}x {item.name}</span>
                    <span>${item.total:.2f}</span>
                </div>
            """
            for modifier in item.modifiers:
                html += f'<div class="modifier">+ {modifier}</div>'
        
        html += f"""
            </div>
            
            <div class="totals">
                <div class="total-line">
                    <span>Subtotal:</span>
                    <span>${receipt_data.subtotal:.2f}</span>
                </div>
                {f'<div class="total-line"><span>Discount:</span><span>-${receipt_data.discount_amount:.2f}</span></div>' if receipt_data.discount_amount > 0 else ''}
                <div class="total-line">
                    <span>Tax ({receipt_data.tax_rate * 100:.1f}%):</span>
                    <span>${receipt_data.tax_amount:.2f}</span>
                </div>
                {f'<div class="total-line"><span>Tip:</span><span>${receipt_data.tip_amount:.2f}</span></div>' if receipt_data.tip_amount > 0 else ''}
                <div class="total-line grand-total">
                    <span>TOTAL:</span>
                    <span>${receipt_data.total_amount:.2f}</span>
                </div>
                <div class="total-line" style="margin-top: 10px;">
                    <span>Payment Method:</span>
                    <span>{receipt_data.payment_method.upper()}</span>
                </div>
            </div>
            
            <div class="footer">
                {receipt_data.footer_message}
            </div>
        </body>
        </html>
        """
        
        return html
    
    async def generate_receipt_pdf(self, receipt_id: UUID) -> bytes:
        """Generate PDF receipt (placeholder for future implementation)"""
        receipt = await self.db.get_receipt(receipt_id)
        if not receipt:
            raise ValueError(f"Receipt {receipt_id} not found")
        
        receipt_data = ReceiptData(**receipt["receipt_data"])
        html = self.generate_receipt_html(receipt_data)
        
        # TODO: Implement PDF generation using weasyprint or reportlab
        # For now, return HTML as bytes
        return html.encode('utf-8')


# Singleton instance
_receipt_generator: Optional[ReceiptGenerator] = None


def get_receipt_generator() -> ReceiptGenerator:
    """Get receipt generator singleton"""
    global _receipt_generator
    if _receipt_generator is None:
        db_service = get_database_service()
        _receipt_generator = ReceiptGenerator(db_service)
    return _receipt_generator
