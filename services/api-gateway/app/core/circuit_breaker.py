"""
Circuit Breaker Implementation

Implements the circuit breaker pattern to prevent cascading failures
and provide fallback mechanisms for failing services.
"""

import logging
import time
from enum import Enum
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from app.config.settings import get_settings

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker for a single service
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Service is failing, requests are blocked
    - HALF_OPEN: Testing if service has recovered
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        timeout: int = 60,
        recovery_timeout: int = 30
    ):
        """
        Initialize circuit breaker
        
        Args:
            name: Service name
            failure_threshold: Number of failures before opening
            timeout: Seconds before transitioning to half-open
            recovery_timeout: Seconds in half-open before re-opening
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.recovery_timeout = recovery_timeout
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.last_state_change: float = time.time()
        self.consecutive_successes = 0
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker
        
        Args:
            func: Function to execute
            *args, **kwargs: Function arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is open or function fails
        """
        # Check circuit state
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._transition_to_half_open()
            else:
                raise Exception(f"Circuit breaker '{self.name}' is OPEN")
        
        try:
            # Execute function
            result = func(*args, **kwargs)
            self._on_success()
            return result
        
        except Exception as e:
            self._on_failure()
            raise
    
    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute async function through circuit breaker
        
        Args:
            func: Async function to execute
            *args, **kwargs: Function arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is open or function fails
        """
        # Check circuit state
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._transition_to_half_open()
            else:
                raise Exception(f"Circuit breaker '{self.name}' is OPEN")
        
        try:
            # Execute async function
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Handle successful call"""
        self.consecutive_successes += 1
        
        if self.state == CircuitState.HALF_OPEN:
            # If we get enough successes in half-open, close the circuit
            if self.consecutive_successes >= 3:
                self._transition_to_closed()
        
        # Reset failure count on success
        if self.consecutive_successes >= 5:
            self.failure_count = max(0, self.failure_count - 1)
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.consecutive_successes = 0
        self.last_failure_time = time.time()
        
        logger.warning(
            f"Circuit breaker '{self.name}' failure count: {self.failure_count}/{self.failure_threshold}"
        )
        
        if self.state == CircuitState.HALF_OPEN:
            # Immediately open if failure in half-open
            self._transition_to_open()
        
        elif self.failure_count >= self.failure_threshold:
            # Open circuit if threshold exceeded
            self._transition_to_open()
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt to reset to half-open"""
        if self.last_failure_time is None:
            return False
        
        time_since_open = time.time() - self.last_failure_time
        return time_since_open >= self.timeout
    
    def _transition_to_closed(self):
        """Transition to CLOSED state"""
        logger.info(f"Circuit breaker '{self.name}' transitioning to CLOSED")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.consecutive_successes = 0
        self.last_state_change = time.time()
    
    def _transition_to_open(self):
        """Transition to OPEN state"""
        logger.error(f"Circuit breaker '{self.name}' transitioning to OPEN")
        self.state = CircuitState.OPEN
        self.consecutive_successes = 0
        self.last_state_change = time.time()
    
    def _transition_to_half_open(self):
        """Transition to HALF_OPEN state"""
        logger.info(f"Circuit breaker '{self.name}' transitioning to HALF_OPEN")
        self.state = CircuitState.HALF_OPEN
        self.consecutive_successes = 0
        self.last_state_change = time.time()
    
    def reset(self):
        """Manually reset circuit breaker to CLOSED"""
        logger.info(f"Manually resetting circuit breaker '{self.name}'")
        self._transition_to_closed()
    
    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "consecutive_successes": self.consecutive_successes,
            "last_failure_time": (
                datetime.fromtimestamp(self.last_failure_time).isoformat()
                if self.last_failure_time else None
            ),
            "last_state_change": datetime.fromtimestamp(self.last_state_change).isoformat()
        }


class CircuitBreakerManager:
    """
    Manages circuit breakers for all services
    """
    
    def __init__(self):
        self.settings = get_settings()
        self._breakers: Dict[str, CircuitBreaker] = {}
    
    def get_breaker(self, service_name: str) -> CircuitBreaker:
        """
        Get or create circuit breaker for service
        
        Args:
            service_name: Service name
            
        Returns:
            CircuitBreaker instance
        """
        if service_name not in self._breakers:
            self._breakers[service_name] = CircuitBreaker(
                name=service_name,
                failure_threshold=self.settings.circuit_breaker_failure_threshold,
                timeout=self.settings.circuit_breaker_timeout,
                recovery_timeout=self.settings.circuit_breaker_recovery_timeout
            )
        
        return self._breakers[service_name]
    
    def reset_breaker(self, service_name: str) -> bool:
        """
        Reset circuit breaker for service
        
        Args:
            service_name: Service name
            
        Returns:
            bool: True if reset successful
        """
        if service_name in self._breakers:
            self._breakers[service_name].reset()
            return True
        return False
    
    def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """Get states of all circuit breakers"""
        return {
            name: breaker.get_state()
            for name, breaker in self._breakers.items()
        }
    
    def get_open_circuits(self) -> list[str]:
        """Get list of services with open circuits"""
        return [
            name for name, breaker in self._breakers.items()
            if breaker.state == CircuitState.OPEN
        ]
