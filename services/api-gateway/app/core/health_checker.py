"""
Health Checker

Periodically checks health of all registered services and updates
their status in the service registry.
"""

import logging
import asyncio
import aiohttp
from typing import Dict, Any
from datetime import datetime
from app.config.settings import get_settings

logger = logging.getLogger(__name__)


class HealthChecker:
    """
    Periodic health checker for all registered services
    """
    
    def __init__(self, service_registry, circuit_breaker_manager):
        """
        Initialize health checker
        
        Args:
            service_registry: ServiceRegistry instance
            circuit_breaker_manager: CircuitBreakerManager instance
        """
        self.settings = get_settings()
        self.service_registry = service_registry
        self.circuit_breaker_manager = circuit_breaker_manager
        self._running = False
        self._task: asyncio.Task = None
    
    async def start(self):
        """Start health checking loop"""
        if not self.settings.health_check_enabled:
            logger.info("Health checking disabled")
            return
        
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._health_check_loop())
        logger.info("Health checker started")
    
    async def stop(self):
        """Stop health checking loop"""
        if not self._running:
            return
        
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("Health checker stopped")
    
    async def _health_check_loop(self):
        """Main health checking loop"""
        while self._running:
            try:
                await self._check_all_services()
                await asyncio.sleep(self.settings.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check loop error: {e}", exc_info=True)
                await asyncio.sleep(5)  # Back off on error
    
    async def _check_all_services(self):
        """Check health of all registered services"""
        services = self.service_registry.get_all_services()
        
        # Check all services concurrently
        tasks = [
            self.check_service_health(service_name)
            for service_name in services
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def check_service_health(self, service_name: str) -> Dict[str, Any]:
        """
        Check health of a specific service
        
        Args:
            service_name: Service name
            
        Returns:
            Health check result
        """
        service = self.service_registry.get_service(service_name)
        if not service:
            return {"healthy": False, "error": "Service not found"}
        
        service_url = service["url"]
        metadata = service.get("metadata", {})
        health_endpoint = metadata.get("health_endpoint", "/health")
        timeout = metadata.get("timeout", self.settings.health_check_timeout)
        
        health_url = f"{service_url}{health_endpoint}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    health_url,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    healthy = response.status == 200
                    
                    # Update service registry
                    self.service_registry.update_service_health(
                        service_name,
                        healthy,
                        datetime.utcnow().isoformat()
                    )
                    
                    # If service is healthy, reset circuit breaker
                    if healthy:
                        breaker = self.circuit_breaker_manager.get_breaker(service_name)
                        if breaker.state != "closed":
                            logger.info(f"Service {service_name} recovered, resetting circuit breaker")
                    
                    result = {
                        "healthy": healthy,
                        "status_code": response.status,
                        "last_check": datetime.utcnow().isoformat()
                    }
                    
                    if not healthy:
                        logger.warning(f"Service {service_name} unhealthy: {response.status}")
                    
                    return result
        
        except asyncio.TimeoutError:
            logger.error(f"Health check timeout for {service_name}")
            self.service_registry.update_service_health(
                service_name,
                False,
                datetime.utcnow().isoformat()
            )
            return {
                "healthy": False,
                "error": "Timeout",
                "last_check": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Health check failed for {service_name}: {e}")
            self.service_registry.update_service_health(
                service_name,
                False,
                datetime.utcnow().isoformat()
            )
            return {
                "healthy": False,
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }
    
    async def get_overall_health(self) -> Dict[str, Any]:
        """
        Get overall health status of all services
        
        Returns:
            Overall health summary
        """
        services = self.service_registry.get_all_services()
        healthy_services = self.service_registry.get_healthy_services()
        
        return {
            "healthy": len(healthy_services) == len(services),
            "total_services": len(services),
            "healthy_services": len(healthy_services),
            "unhealthy_services": len(services) - len(healthy_services),
            "services": {
                service: self.service_registry.is_service_healthy(service)
                for service in services
            },
            "timestamp": datetime.utcnow().isoformat()
        }
