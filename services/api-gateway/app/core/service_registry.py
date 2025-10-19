"""
Service Registry

Manages the registry of all backend microservices with their URLs,
health status, and metadata. Supports static and dynamic service discovery.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.config.settings import get_settings

logger = logging.getLogger(__name__)


class ServiceRegistry:
    """
    Centralized service registry for all backend microservices.
    
    Features:
    - Service registration and deregistration
    - Service metadata management
    - Health status tracking
    - Service discovery
    """
    
    def __init__(self):
        self.settings = get_settings()
        self._services: Dict[str, Dict[str, Any]] = {}
        self._initialized = False
    
    async def initialize(self):
        """Initialize service registry with configured services"""
        if self._initialized:
            return
        
        # Register all configured services
        services_config = [
            {
                "name": "auth-service",
                "url": self.settings.auth_service_url,
                "health_endpoint": "/health",
                "timeout": self.settings.default_request_timeout,
                "priority": 1
            },
            {
                "name": "business-logic-service",
                "url": self.settings.business_logic_service_url,
                "health_endpoint": "/health",
                "timeout": self.settings.default_request_timeout,
                "priority": 2
            },
            {
                "name": "ai-orchestration-service",
                "url": self.settings.ai_orchestration_service_url,
                "health_endpoint": "/api/v1/health",
                "timeout": self.settings.ai_request_timeout,
                "priority": 2
            },
            {
                "name": "chat-communication-service",
                "url": self.settings.chat_communication_service_url,
                "health_endpoint": "/health",
                "timeout": self.settings.default_request_timeout,
                "priority": 2
            },
            {
                "name": "analytics-dashboard-service",
                "url": self.settings.analytics_dashboard_service_url,
                "health_endpoint": "/health",
                "timeout": self.settings.analytics_request_timeout,
                "priority": 3
            },
            {
                "name": "notification-integration-service",
                "url": self.settings.notification_integration_service_url,
                "health_endpoint": "/health",
                "timeout": self.settings.default_request_timeout,
                "priority": 2
            },
            {
                "name": "global-chat-service",
                "url": self.settings.global_chat_service_url,
                "health_endpoint": "/health",
                "timeout": self.settings.default_request_timeout,
                "priority": 2
            },
            {
                "name": "dedicated-business-chat-service",
                "url": self.settings.dedicated_business_chat_service_url,
                "health_endpoint": "/health",
                "timeout": self.settings.default_request_timeout,
                "priority": 2
            },
            {
                "name": "pos-service",
                "url": self.settings.pos_service_url,
                "health_endpoint": "/health",
                "timeout": self.settings.default_request_timeout,
                "priority": 3
            },
            {
                "name": "template-selection-service",
                "url": self.settings.template_selection_service_url,
                "health_endpoint": "/health",
                "timeout": self.settings.default_request_timeout,
                "priority": 3
            },
            {
                "name": "monitoring-logging-service",
                "url": self.settings.monitoring_logging_service_url,
                "health_endpoint": "/health",
                "timeout": self.settings.default_request_timeout,
                "priority": 4
            },
            {
                "name": "devops-service",
                "url": self.settings.devops_service_url,
                "health_endpoint": "/health",
                "timeout": self.settings.default_request_timeout,
                "priority": 4
            }
        ]
        
        for service_config in services_config:
            await self.register_service(
                name=service_config["name"],
                url=service_config["url"],
                metadata={
                    "health_endpoint": service_config["health_endpoint"],
                    "timeout": service_config["timeout"],
                    "priority": service_config["priority"],
                    "registered_at": datetime.utcnow().isoformat()
                }
            )
        
        self._initialized = True
        logger.info(f"Service registry initialized with {len(self._services)} services")
    
    async def register_service(
        self,
        name: str,
        url: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Register a new service
        
        Args:
            name: Service name
            url: Service base URL
            metadata: Additional service metadata
            
        Returns:
            bool: True if registration successful
        """
        if not name or not url:
            logger.error(f"Invalid service registration: name={name}, url={url}")
            return False
        
        self._services[name] = {
            "name": name,
            "url": url.rstrip('/'),
            "metadata": metadata or {},
            "registered_at": datetime.utcnow().isoformat(),
            "healthy": True,
            "last_health_check": None
        }
        
        logger.info(f"Registered service: {name} at {url}")
        return True
    
    def deregister_service(self, name: str) -> bool:
        """
        Deregister a service
        
        Args:
            name: Service name
            
        Returns:
            bool: True if deregistration successful
        """
        if name in self._services:
            del self._services[name]
            logger.info(f"Deregistered service: {name}")
            return True
        return False
    
    def get_service(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get service by name
        
        Args:
            name: Service name
            
        Returns:
            Service information or None
        """
        return self._services.get(name)
    
    def get_all_services(self) -> List[str]:
        """Get list of all registered service names"""
        return list(self._services.keys())
    
    def get_service_url(self, name: str) -> Optional[str]:
        """
        Get service URL by name
        
        Args:
            name: Service name
            
        Returns:
            Service URL or None
        """
        service = self._services.get(name)
        return service["url"] if service else None
    
    def update_service_health(
        self,
        name: str,
        healthy: bool,
        last_check_time: Optional[str] = None
    ):
        """
        Update service health status
        
        Args:
            name: Service name
            healthy: Health status
            last_check_time: Last health check timestamp
        """
        if name in self._services:
            self._services[name]["healthy"] = healthy
            self._services[name]["last_health_check"] = (
                last_check_time or datetime.utcnow().isoformat()
            )
    
    def is_service_healthy(self, name: str) -> bool:
        """
        Check if service is healthy
        
        Args:
            name: Service name
            
        Returns:
            bool: True if healthy
        """
        service = self._services.get(name)
        return service.get("healthy", False) if service else False
    
    def get_healthy_services(self) -> List[str]:
        """Get list of all healthy services"""
        return [
            name for name, service in self._services.items()
            if service.get("healthy", False)
        ]
    
    def get_service_metadata(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get service metadata
        
        Args:
            name: Service name
            
        Returns:
            Service metadata or None
        """
        service = self._services.get(name)
        return service.get("metadata") if service else None
    
    def update_service_metadata(
        self,
        name: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Update service metadata
        
        Args:
            name: Service name
            metadata: Metadata to update
            
        Returns:
            bool: True if update successful
        """
        if name in self._services:
            self._services[name]["metadata"].update(metadata)
            return True
        return False
    
    def get_service_by_priority(self, min_priority: int = 1) -> List[str]:
        """
        Get services by priority
        
        Args:
            min_priority: Minimum priority level
            
        Returns:
            List of service names sorted by priority
        """
        services_with_priority = [
            (name, service["metadata"].get("priority", 999))
            for name, service in self._services.items()
            if service["metadata"].get("priority", 999) >= min_priority
        ]
        
        # Sort by priority (lower number = higher priority)
        services_with_priority.sort(key=lambda x: x[1])
        
        return [name for name, _ in services_with_priority]
