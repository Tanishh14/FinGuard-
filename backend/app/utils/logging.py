"""
Logging configuration for FinGuard AI
"""

import sys
import time
from typing import Dict, Any
from loguru import logger
import json
from fastapi import Request, Response

from app.core.config import settings


def setup_logging():
    """Configure loguru logging"""
    
    # Remove default handler
    logger.remove()
    
    # Add console handler
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.LOG_LEVEL,
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # Add file handler for errors
    logger.add(
        "logs/error.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="500 MB",
        compression="zip",
        backtrace=True,
        diagnose=True
    )
    
    # Add file handler for all logs
    logger.add(
        "logs/app.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        level="INFO",
        rotation="500 MB",
        compression="zip"
    )
    
    # Add JSON handler for structured logging (for production)
    if settings.ENVIRONMENT == "production":
        logger.add(
            "logs/structured.log",
            format=format_json_log,
            level="INFO",
            rotation="500 MB",
            compression="zip",
            serialize=True
        )
    
    logger.info(f"Logging configured with level: {settings.LOG_LEVEL}")


def format_json_log(record: Dict[str, Any]) -> str:
    """Format log record as JSON for structured logging"""
    
    # Extract relevant fields
    log_entry = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "message": record["message"],
        "module": record["name"],
        "function": record["function"],
        "line": record["line"],
        "process": record["process"].id,
        "thread": record["thread"].id,
    }
    
    # Add exception info if present
    if record["exception"]:
        log_entry["exception"] = {
            "type": str(record["exception"].type),
            "value": str(record["exception"].value),
            "traceback": record["exception"].traceback.format()
        }
    
    # Add extra fields if present
    if record["extra"]:
        log_entry["extra"] = record["extra"]
    
    return json.dumps(log_entry)


async def log_request(request: Request, response: Response, process_time: float):
    """Log HTTP requests with details"""
    
    # Skip health checks and static files in production
    if settings.ENVIRONMENT == "production" and request.url.path in ["/health", "/favicon.ico"]:
        return
    
    # Build log data
    log_data = {
        "method": request.method,
        "url": str(request.url),
        "status_code": response.status_code,
        "process_time": round(process_time * 1000, 2),  # Convert to ms
        "client_ip": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", ""),
    }
    
    # Add user info if available
    if hasattr(request.state, "user"):
        log_data["user_id"] = str(request.state.user.id)
    
    # Log based on status code
    if response.status_code >= 500:
        logger.error("Server error", **log_data)
    elif response.status_code >= 400:
        logger.warning("Client error", **log_data)
    else:
        logger.info("Request processed", **log_data)


class RequestIdFilter:
    """Add request ID to logs for request tracing"""
    
    def __init__(self):
        import uuid
        self.request_id = str(uuid.uuid4())
    
    def __call__(self, record):
        record["extra"]["request_id"] = self.request_id
        return True


# Context manager for request-specific logging
class RequestLogger:
    """Context manager for request-specific logging"""
    
    def __init__(self, request_id: str = None):
        import uuid
        self.request_id = request_id or str(uuid.uuid4())
        self.filter = None
    
    def __enter__(self):
        self.filter = RequestIdFilter()
        logger.configure(extra={"request_id": self.filter.request_id})
        logger.bind(request_id=self.filter.request_id)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        logger.unbind("request_id")
    
    def get_request_id(self) -> str:
        return self.filter.request_id if self.filter else "unknown"