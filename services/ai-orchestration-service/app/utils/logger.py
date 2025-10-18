"""
Structured logging utility for AI Orchestration Service

Provides JSON-formatted logging with context and trace IDs for observability.
"""

import logging
import sys
from typing import Any, Dict, Optional
from pythonjsonlogger import jsonlogger
from datetime import datetime
import uuid


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional context"""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp
        log_record['timestamp'] = datetime.utcnow().isoformat()
        
        # Add service name
        log_record['service'] = 'ai-orchestration-service'
        
        # Add log level
        log_record['level'] = record.levelname
        
        # Add trace ID if available
        if hasattr(record, 'trace_id'):
            log_record['trace_id'] = record.trace_id
        
        # Add user ID if available
        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id


def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    Set up a structured JSON logger
    
    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    
    # Set JSON formatter
    formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    
    return logger


class LoggerAdapter(logging.LoggerAdapter):
    """Logger adapter for adding context to log messages"""
    
    def __init__(self, logger: logging.Logger, extra: Optional[Dict[str, Any]] = None):
        super().__init__(logger, extra or {})
        self.trace_id = str(uuid.uuid4())
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Add trace_id to log records"""
        if 'extra' not in kwargs:
            kwargs['extra'] = {}
        kwargs['extra']['trace_id'] = self.trace_id
        if self.extra:
            kwargs['extra'].update(self.extra)
        return msg, kwargs
    
    def with_context(self, **context: Any) -> 'LoggerAdapter':
        """Create a new adapter with additional context"""
        new_extra = {**self.extra, **context}
        adapter = LoggerAdapter(self.logger, new_extra)
        adapter.trace_id = self.trace_id
        return adapter


# Default logger instance
logger = setup_logger("ai-orchestration")
