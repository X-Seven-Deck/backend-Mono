"""
Helper functions for the Auth Service.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict

logger = logging.getLogger(__name__)

def generate_uuid() -> str:
    """
    Generate a UUID.
    
    Returns:
        UUID string.
    """
    return str(uuid.uuid4())

def format_datetime(dt: datetime) -> str:
    """
    Format a datetime object to ISO format.
    
    Args:
        dt: Datetime object.
        
    Returns:
        Formatted datetime string.
    """
    return dt.isoformat()

def log_error(error: Exception, context: Dict[str, Any] = None) -> None:
    """
    Log an error with context.
    
    Args:
        error: Exception object.
        context: Additional context.
    """
    error_data = {
        "error": str(error),
        "error_type": type(error).__name__,
    }
    
    if context:
        error_data.update(context)
    
    logger.error(f"Error: {error_data}")

def sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize a dictionary by removing None values.
    
    Args:
        data: Dictionary to sanitize.
        
    Returns:
        Sanitized dictionary.
    """
    return {k: v for k, v in data.items() if v is not None}
