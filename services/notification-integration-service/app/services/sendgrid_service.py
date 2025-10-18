"""
SendGrid Service for email notifications
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, Attachment, FileContent, FileName, FileType, Disposition
from python_http_client.exceptions import HTTPError

from app.config import settings
from app.utils import logger


class SendGridService:
    """
    Enterprise-grade SendGrid service for email notifications
    
    Features:
    - Transactional emails
    - Template-based emails
    - Bulk email support
    - Attachment handling
    - Email tracking and analytics
    """
    
    def __init__(self):
        self.client: Optional[SendGridAPIClient] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize SendGrid client"""
        if self._initialized:
            return
        
        try:
            if not settings.sendgrid_api_key:
                logger.warning("SendGrid API key not configured")
                return
            
            self.client = SendGridAPIClient(api_key=settings.sendgrid_api_key)
            
            logger.info("SendGrid service initialized successfully")
            self._initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize SendGrid: {e}", exc_info=True)
            raise
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        plain_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        custom_args: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Send email
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            plain_content: Plain text content (fallback)
            from_email: Sender email (defaults to configured)
            from_name: Sender name (defaults to configured)
            attachments: List of attachments
            custom_args: Custom tracking arguments
        
        Returns:
            Dictionary with send status
        """
        if not self._initialized:
            await self.initialize()
        
        if not self.client:
            raise RuntimeError("SendGrid client not initialized")
        
        try:
            logger.info(f"Sending email to {to_email}")
            
            # Create message
            message = Mail(
                from_email=Email(
                    from_email or settings.sendgrid_from_email,
                    from_name or settings.sendgrid_from_name
                ),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content)
            )
            
            # Add plain text content if provided
            if plain_content:
                message.add_content(Content("text/plain", plain_content))
            
            # Add attachments
            if attachments:
                for attachment_data in attachments:
                    attachment = Attachment(
                        FileContent(attachment_data.get("content")),
                        FileName(attachment_data.get("filename")),
                        FileType(attachment_data.get("type", "application/octet-stream")),
                        Disposition(attachment_data.get("disposition", "attachment"))
                    )
                    message.add_attachment(attachment)
            
            # Add custom tracking args
            if custom_args:
                message.custom_arg = custom_args
            
            # Send email
            response = self.client.send(message)
            
            logger.info(f"Email sent successfully to {to_email}. Status: {response.status_code}")
            
            return {
                "status": "success",
                "to": to_email,
                "subject": subject,
                "status_code": response.status_code,
                "message_id": response.headers.get("X-Message-Id"),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except HTTPError as e:
            logger.error(f"SendGrid HTTP error: {e.body}", exc_info=True)
            return {
                "status": "error",
                "error": e.body,
                "to": to_email,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Email sending error: {e}", exc_info=True)
            raise
    
    async def send_template_email(
        self,
        to_email: str,
        template_id: str,
        dynamic_data: Dict[str, Any],
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send email using SendGrid template
        
        Args:
            to_email: Recipient email address
            template_id: SendGrid template ID
            dynamic_data: Template variables
            from_email: Sender email
            from_name: Sender name
        
        Returns:
            Dictionary with send status
        """
        if not self._initialized:
            await self.initialize()
        
        if not self.client:
            raise RuntimeError("SendGrid client not initialized")
        
        try:
            logger.info(f"Sending template email to {to_email} using template {template_id}")
            
            message = Mail(
                from_email=Email(
                    from_email or settings.sendgrid_from_email,
                    from_name or settings.sendgrid_from_name
                ),
                to_emails=To(to_email)
            )
            
            message.template_id = template_id
            message.dynamic_template_data = dynamic_data
            
            response = self.client.send(message)
            
            logger.info(f"Template email sent successfully to {to_email}")
            
            return {
                "status": "success",
                "to": to_email,
                "template_id": template_id,
                "status_code": response.status_code,
                "message_id": response.headers.get("X-Message-Id"),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except HTTPError as e:
            logger.error(f"SendGrid template error: {e.body}", exc_info=True)
            return {
                "status": "error",
                "error": e.body,
                "to": to_email,
                "template_id": template_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Template email error: {e}", exc_info=True)
            raise
    
    async def send_bulk_email(
        self,
        recipients: List[Dict[str, Any]],
        subject: str,
        html_content: str,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Send bulk emails
        
        Args:
            recipients: List of recipient dictionaries with 'email' and optional 'name'
            subject: Email subject
            html_content: HTML content
            batch_size: Number of emails to send concurrently
        
        Returns:
            Dictionary with success/failure counts
        """
        if not self._initialized:
            await self.initialize()
        
        logger.info(f"Sending bulk email to {len(recipients)} recipients")
        
        results = {
            "total": len(recipients),
            "success": 0,
            "failed": 0,
            "details": []
        }
        
        # Process in batches
        for i in range(0, len(recipients), batch_size):
            batch = recipients[i:i + batch_size]
            
            # Send emails concurrently
            tasks = [
                self.send_email(
                    to_email=recipient.get("email"),
                    subject=subject,
                    html_content=html_content
                )
                for recipient in batch
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    results["failed"] += 1
                    results["details"].append({"error": str(result)})
                elif result.get("status") == "success":
                    results["success"] += 1
                    results["details"].append(result)
                else:
                    results["failed"] += 1
                    results["details"].append(result)
            
            # Rate limiting delay
            if i + batch_size < len(recipients):
                await asyncio.sleep(0.5)
        
        logger.info(f"Bulk email complete: {results['success']} success, {results['failed']} failed")
        
        return results


# Global SendGrid service instance
sendgrid_service = SendGridService()
