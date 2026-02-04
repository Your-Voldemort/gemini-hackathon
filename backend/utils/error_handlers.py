"""
Error Handling & Response Standardization
Provides consistent error responses and logging
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from datetime import datetime
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Standard API error for consistent error responses."""
    
    def __init__(
        self,
        status_code: int,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        log_level: str = "warning"
    ):
        self.status_code = status_code
        self.message = message
        self.details = details or {}
        self.log_level = log_level
        
        # Log the error
        log_func = getattr(logger, log_level, logger.warning)
        log_func(f"API Error {status_code}: {message}", extra={"details": self.details})
        
        super().__init__(self.message)


def get_error_response(
    status_code: int,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    include_details: bool = False
) -> Dict[str, Any]:
    """Create a standardized error response.
    
    Args:
        status_code: HTTP status code
        message: User-friendly error message
        details: Technical details (only included if include_details=True)
        include_details: Whether to include technical details (for debugging)
        
    Returns:
        Standardized error response dict
    """
    response = {
        "success": False,
        "status": "error",
        "error": message,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    if include_details and details:
        response["details"] = details
    
    return response


# Error message mapping for common HTTP status codes
ERROR_MESSAGES = {
    400: "Invalid request. Please check your input.",
    401: "Authentication required.",
    403: "Access denied.",
    404: "Resource not found.",
    429: "Too many requests. Please wait a moment.",
    500: "Server error. We're working on it.",
    503: "Service temporarily unavailable. Try again soon.",
    504: "Request timeout. The operation took too long.",
}


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):
    """Handle validation errors with user-friendly messages."""
    logger.warning(f"Validation error: {exc}")
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=get_error_response(
            status_code=400,
            message="Invalid request format. Please check your input.",
            details={"errors": [str(e) for e in exc.errors()]},
            include_details=True
        )
    )


async def api_error_handler(request: Request, exc: APIError):
    """Handle custom API errors."""
    return JSONResponse(
        status_code=exc.status_code,
        content=get_error_response(
            status_code=exc.status_code,
            message=exc.message,
            details=exc.details,
            include_details=False
        )
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=get_error_response(
            status_code=500,
            message="An unexpected error occurred. Please try again.",
        )
    )
