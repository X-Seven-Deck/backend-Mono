"""
HashiCorp Vault Integration Service

Enterprise secrets management with dynamic credentials and encryption.
"""

import os
from typing import Dict, Optional, Any
import logging
import httpx
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class VaultService:
    """
    HashiCorp Vault integration for secrets management.
    
    Features:
    - Dynamic database credentials with auto-rotation
    - API key management
    - Encryption as a Service
    - Audit logging for all secret access
    """
    
    def __init__(self):
        self.vault_addr = os.getenv("VAULT_ADDR", "http://vault:8200")
        self.vault_token = os.getenv("VAULT_TOKEN", "x7ai-root-token")
        self.vault_namespace = os.getenv("VAULT_NAMESPACE", "x7ai")
        
        self._client = httpx.AsyncClient(
            base_url=self.vault_addr,
            headers={
                "X-Vault-Token": self.vault_token,
                "X-Vault-Namespace": self.vault_namespace
            },
            timeout=10.0
        )
    
    async def get_database_credentials(
        self,
        role: str = "app-role",
        tenant_id: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Get dynamic database credentials with auto-rotation.
        
        Vault generates temporary credentials that expire after TTL.
        """
        try:
            # For tenant-specific credentials, use tenant role
            if tenant_id:
                role = f"tenant-{tenant_id}"
            
            response = await self._client.get(
                f"/v1/database/creds/{role}"
            )
            
            if response.status_code == 200:
                data = response.json()
                credentials = data.get("data", {})
                
                logger.info(
                    f"Generated database credentials for role {role}, "
                    f"lease_id: {data.get('lease_id')}"
                )
                
                return {
                    "username": credentials.get("username"),
                    "password": credentials.get("password"),
                    "lease_id": data.get("lease_id"),
                    "lease_duration": data.get("lease_duration"),
                    "renewable": data.get("renewable", False)
                }
            else:
                logger.error(f"Failed to get credentials: {response.status_code}")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting database credentials: {e}")
            return {}
    
    async def get_api_key(
        self,
        service: str,
        tenant_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Retrieve API key for external service.
        
        Supports:
        - OpenAI API keys
        - Twilio credentials
        - SendGrid API keys
        - Stripe keys
        - etc.
        """
        try:
            # Build secret path
            if tenant_id:
                path = f"secret/data/tenants/{tenant_id}/{service}"
            else:
                path = f"secret/data/api-keys/{service}"
            
            response = await self._client.get(f"/v1/{path}")
            
            if response.status_code == 200:
                data = response.json()
                secret_data = data.get("data", {}).get("data", {})
                
                logger.info(f"Retrieved API key for {service}")
                
                return secret_data.get("api_key") or secret_data.get("key")
            else:
                logger.warning(f"API key not found for {service}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting API key: {e}")
            return None
    
    async def store_api_key(
        self,
        service: str,
        api_key: str,
        tenant_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Store API key securely in Vault.
        """
        try:
            # Build secret path
            if tenant_id:
                path = f"secret/data/tenants/{tenant_id}/{service}"
            else:
                path = f"secret/data/api-keys/{service}"
            
            payload = {
                "data": {
                    "api_key": api_key,
                    "created_at": datetime.utcnow().isoformat(),
                    **(metadata or {})
                }
            }
            
            response = await self._client.post(f"/v1/{path}", json=payload)
            
            if response.status_code in [200, 204]:
                logger.info(f"Stored API key for {service}")
                return True
            else:
                logger.error(f"Failed to store API key: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error storing API key: {e}")
            return False
    
    async def encrypt_data(
        self,
        plaintext: str,
        key_name: str = "tenant-encryption-key"
    ) -> Optional[str]:
        """
        Encrypt data using Vault's Transit engine.
        
        Encryption as a Service - Vault handles key management.
        """
        try:
            payload = {
                "plaintext": plaintext
            }
            
            response = await self._client.post(
                f"/v1/transit/encrypt/{key_name}",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                ciphertext = data.get("data", {}).get("ciphertext")
                
                logger.debug(f"Encrypted data with key {key_name}")
                
                return ciphertext
            else:
                logger.error(f"Encryption failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error encrypting data: {e}")
            return None
    
    async def decrypt_data(
        self,
        ciphertext: str,
        key_name: str = "tenant-encryption-key"
    ) -> Optional[str]:
        """
        Decrypt data using Vault's Transit engine.
        """
        try:
            payload = {
                "ciphertext": ciphertext
            }
            
            response = await self._client.post(
                f"/v1/transit/decrypt/{key_name}",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                plaintext = data.get("data", {}).get("plaintext")
                
                logger.debug(f"Decrypted data with key {key_name}")
                
                return plaintext
            else:
                logger.error(f"Decryption failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error decrypting data: {e}")
            return None
    
    async def get_tenant_encryption_key(self, tenant_id: str) -> str:
        """
        Get or create tenant-specific encryption key.
        """
        key_name = f"tenant-{tenant_id}-key"
        
        # Check if key exists
        try:
            response = await self._client.get(f"/v1/transit/keys/{key_name}")
            
            if response.status_code == 200:
                return key_name
            
            # Create key if doesn't exist
            await self._client.post(
                f"/v1/transit/keys/{key_name}",
                json={"type": "aes256-gcm96"}
            )
            
            logger.info(f"Created encryption key for tenant {tenant_id}")
            
            return key_name
            
        except Exception as e:
            logger.error(f"Error managing encryption key: {e}")
            return "default-key"
    
    async def rotate_credentials(self, lease_id: str) -> bool:
        """
        Renew or rotate credentials before expiration.
        """
        try:
            response = await self._client.put(
                "/v1/sys/leases/renew",
                json={"lease_id": lease_id}
            )
            
            if response.status_code == 200:
                logger.info(f"Renewed lease {lease_id}")
                return True
            else:
                logger.error(f"Failed to renew lease: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error rotating credentials: {e}")
            return False
    
    async def revoke_credentials(self, lease_id: str) -> bool:
        """
        Revoke credentials immediately.
        """
        try:
            response = await self._client.put(
                "/v1/sys/leases/revoke",
                json={"lease_id": lease_id}
            )
            
            if response.status_code == 204:
                logger.info(f"Revoked lease {lease_id}")
                return True
            else:
                logger.error(f"Failed to revoke lease: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error revoking credentials: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check Vault health and connectivity"""
        try:
            response = await self._client.get("/v1/sys/health")
            return response.status_code in [200, 429, 472, 473]
        except Exception as e:
            logger.error(f"Vault health check failed: {e}")
            return False
    
    async def close(self):
        """Close HTTP client"""
        await self._client.aclose()


# Singleton instance
_vault_service = None

def get_vault_service() -> VaultService:
    """Get singleton instance of VaultService"""
    global _vault_service
    if _vault_service is None:
        _vault_service = VaultService()
    return _vault_service
