"""
Multi-Factor Authentication Service

Implements comprehensive MFA including:
- TOTP (Time-based One-Time Password)
- SMS OTP
- Email OTP
- Backup codes for recovery
"""

import logging
import secrets
import hashlib
from typing import Optional, List, Tuple
from datetime import datetime
import base64
from io import BytesIO

import pyotp
import qrcode
from passlib.context import CryptContext

logger = logging.getLogger(__name__)

# Password hashing context for backup codes
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class MFAService:
    """
    Enterprise MFA service supporting multiple authentication methods.
    """

    def __init__(self):
        self.totp_issuer = "X7AI"
        self.backup_code_length = 8
        self.backup_code_count = 10

    async def setup_totp(self, user_email: str) -> Tuple[str, str, List[str]]:
        """
        Setup TOTP-based MFA for a user.

        Args:
            user_email: User's email address

        Returns:
            Tuple of (secret, qr_code_data_url, backup_codes)
        """
        # Generate a random secret
        secret = pyotp.random_base32()

        # Create TOTP URI for QR code
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user_email,
            issuer_name=self.totp_issuer
        )

        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        qr_code_data = base64.b64encode(buffered.getvalue()).decode()
        qr_code_data_url = f"data:image/png;base64,{qr_code_data}"

        # Generate backup codes
        backup_codes = self._generate_backup_codes()

        return secret, qr_code_data_url, backup_codes

    async def verify_totp(self, secret: str, code: str, window: int = 1) -> bool:
        """
        Verify a TOTP code.

        Args:
            secret: User's TOTP secret
            code: Code to verify
            window: Number of time steps to check (default: 1 = 30 seconds)

        Returns:
            True if code is valid, False otherwise
        """
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(code, valid_window=window)
        except Exception as e:
            logger.error(f"TOTP verification error: {str(e)}")
            return False

    async def setup_sms(self, phone_number: str) -> str:
        """
        Setup SMS-based MFA.

        Args:
            phone_number: User's phone number

        Returns:
            Verification code sent to phone
        """
        # Generate 6-digit code
        code = self._generate_numeric_code(6)

        # Send SMS (implement with Twilio in production)
        await self._send_sms(phone_number, code)

        return code

    async def setup_email(self, email: str) -> str:
        """
        Setup email-based MFA.

        Args:
            email: User's email address

        Returns:
            Verification code sent to email
        """
        # Generate 6-digit code
        code = self._generate_numeric_code(6)

        # Send email (implement with SendGrid in production)
        await self._send_email(email, code)

        return code

    async def verify_code(self, stored_code: str, provided_code: str) -> bool:
        """
        Verify a numeric code (SMS/Email).

        Args:
            stored_code: Code stored in database
            provided_code: Code provided by user

        Returns:
            True if codes match, False otherwise
        """
        return stored_code == provided_code

    def _generate_backup_codes(self) -> List[str]:
        """
        Generate backup codes for account recovery.

        Returns:
            List of backup codes
        """
        backup_codes = []
        for _ in range(self.backup_code_count):
            code = self._generate_alphanumeric_code(self.backup_code_length)
            backup_codes.append(code)
        return backup_codes

    def hash_backup_code(self, code: str) -> str:
        """
        Hash a backup code for storage.

        Args:
            code: Backup code to hash

        Returns:
            Hashed backup code
        """
        return pwd_context.hash(code)

    def verify_backup_code(self, code: str, hashed_code: str) -> bool:
        """
        Verify a backup code against its hash.

        Args:
            code: Backup code to verify
            hashed_code: Stored hash

        Returns:
            True if code matches, False otherwise
        """
        return pwd_context.verify(code, hashed_code)

    def _generate_numeric_code(self, length: int = 6) -> str:
        """Generate a random numeric code."""
        return ''.join([str(secrets.randbelow(10)) for _ in range(length)])

    def _generate_alphanumeric_code(self, length: int = 8) -> str:
        """Generate a random alphanumeric code."""
        alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # Removed ambiguous chars
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    async def _send_sms(self, phone_number: str, code: str):
        """
        Send SMS with verification code.
        
        In production, implement with Twilio:
        
        from twilio.rest import Client
        
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=f"Your X7AI verification code is: {code}",
            from_=twilio_phone_number,
            to=phone_number
        )
        """
        logger.info(f"SMS code {code} would be sent to {phone_number}")
        # TODO: Implement actual SMS sending in production
        pass

    async def _send_email(self, email: str, code: str):
        """
        Send email with verification code.
        
        In production, implement with SendGrid:
        
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        
        message = Mail(
            from_email='noreply@x7ai.com',
            to_emails=email,
            subject='X7AI Verification Code',
            html_content=f'<p>Your verification code is: <strong>{code}</strong></p>'
        )
        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(message)
        """
        logger.info(f"Email code {code} would be sent to {email}")
        # TODO: Implement actual email sending in production
        pass


class SessionManager:
    """
    Advanced session management with device tracking.
    """

    def __init__(self):
        self.max_sessions_per_user = 5  # Configurable per user tier

    async def create_session(
        self,
        user_id: str,
        device_info: dict,
        ip_address: str,
        remember_me: bool = False
    ) -> dict:
        """
        Create a new session with device tracking.

        Args:
            user_id: User ID
            device_info: Device information (browser, OS, etc.)
            ip_address: Client IP address
            remember_me: Extended session duration

        Returns:
            Session data
        """
        session_data = {
            "user_id": user_id,
            "device_info": device_info,
            "ip_address": ip_address,
            "created_at": datetime.utcnow(),
            "remember_me": remember_me,
            "is_active": True
        }

        # In production, store in Redis or database
        return session_data

    async def get_active_sessions(self, user_id: str) -> List[dict]:
        """
        Get all active sessions for a user.

        Args:
            user_id: User ID

        Returns:
            List of active sessions
        """
        # In production, query from Redis/database
        return []

    async def revoke_session(self, session_id: str):
        """
        Revoke a specific session.

        Args:
            session_id: Session ID to revoke
        """
        # In production, update session status in database
        logger.info(f"Session {session_id} revoked")

    async def revoke_all_sessions(self, user_id: str, except_current: Optional[str] = None):
        """
        Revoke all sessions for a user.

        Args:
            user_id: User ID
            except_current: Current session ID to keep active
        """
        # In production, update all sessions in database
        logger.info(f"All sessions for user {user_id} revoked (except {except_current})")


class APIKeyManager:
    """
    API key generation and management.
    """

    def __init__(self):
        self.key_prefix = "x7ai"
        self.key_length = 32

    def generate_api_key(
        self,
        user_id: str,
        scopes: List[str],
        name: str,
        expires_days: Optional[int] = None
    ) -> Tuple[str, str]:
        """
        Generate a new API key.

        Args:
            user_id: User ID
            scopes: List of permissions
            name: Key name/description
            expires_days: Days until expiration (None = no expiration)

        Returns:
            Tuple of (key, key_id)
        """
        # Generate random key
        random_bytes = secrets.token_bytes(self.key_length)
        key_hash = hashlib.sha256(random_bytes).hexdigest()[:self.key_length]
        
        # Format: x7ai_live_<hash>
        api_key = f"{self.key_prefix}_live_{key_hash}"

        # Generate key ID for storage
        key_id = hashlib.sha256(api_key.encode()).hexdigest()[:16]

        return api_key, key_id

    def hash_api_key(self, api_key: str) -> str:
        """
        Hash an API key for storage.

        Args:
            api_key: API key to hash

        Returns:
            Hashed key
        """
        return hashlib.sha256(api_key.encode()).hexdigest()

    def verify_api_key(self, api_key: str, stored_hash: str) -> bool:
        """
        Verify an API key against its hash.

        Args:
            api_key: API key to verify
            stored_hash: Stored hash

        Returns:
            True if key matches, False otherwise
        """
        computed_hash = self.hash_api_key(api_key)
        return computed_hash == stored_hash


# Global instances
mfa_service = MFAService()
session_manager = SessionManager()
api_key_manager = APIKeyManager()
