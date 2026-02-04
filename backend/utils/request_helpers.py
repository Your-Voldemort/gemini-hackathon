"""
Request Helpers
Utilities for request handling, timeouts, and async operations
"""

import asyncio
from functools import wraps
from typing import Callable, Any, Optional
import logging

logger = logging.getLogger(__name__)


async def with_timeout(
    coro,
    timeout_seconds: float,
    timeout_message: str = "Request timeout"
):
    """Execute an async operation with a timeout.
    
    Args:
        coro: Coroutine to execute
        timeout_seconds: Timeout in seconds
        timeout_message: Message to include in timeout error
        
    Returns:
        Result of the coroutine
        
    Raises:
        asyncio.TimeoutError: If the operation exceeds the timeout
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        logger.error(f"Request timeout after {timeout_seconds}s: {timeout_message}")
        raise


def timeout_handler(timeout_seconds: float):
    """Decorator to add timeout to async functions.
    
    Args:
        timeout_seconds: Timeout in seconds
        
    Example:
        @timeout_handler(30)
        async def my_function():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await with_timeout(
                func(*args, **kwargs),
                timeout_seconds,
                f"{func.__name__} exceeded {timeout_seconds}s timeout"
            )
        return wrapper
    return decorator


async def with_retry(
    coro_func: Callable,
    max_retries: int = 3,
    delay_seconds: float = 1.0,
    backoff_multiplier: float = 2.0
):
    """Execute an async operation with exponential backoff retry.
    
    Args:
        coro_func: Async callable that returns a coroutine
        max_retries: Maximum number of retry attempts
        delay_seconds: Initial delay between retries in seconds
        backoff_multiplier: Multiplier for delay on each retry
        
    Returns:
        Result of the coroutine
        
    Raises:
        Exception: If all retries fail
    """
    delay = delay_seconds
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            return await coro_func()
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries} failed, "
                    f"retrying in {delay}s: {str(e)}"
                )
                await asyncio.sleep(delay)
                delay *= backoff_multiplier
            else:
                logger.error(f"All {max_retries} attempts failed: {str(e)}")
    
    raise last_exception if last_exception else Exception("Unknown error")


def validate_request_size(
    max_size_mb: float = 10.0
):
    """Middleware to validate request body size.
    
    Args:
        max_size_mb: Maximum allowed request size in MB
        
    Returns:
        Middleware function
    """
    max_bytes = int(max_size_mb * 1024 * 1024)
    
    async def middleware(request, call_next):
        content_length = request.headers.get("content-length", 0)
        try:
            content_length = int(content_length)
        except (ValueError, TypeError):
            content_length = 0
        
        if content_length > max_bytes:
            logger.warning(
                f"Request rejected: size {content_length} bytes "
                f"exceeds limit of {max_bytes} bytes"
            )
            return JSONResponse(
                status_code=413,
                content={
                    "success": False,
                    "error": f"Request too large. Maximum size: {max_size_mb}MB"
                }
            )
        
        return await call_next(request)
    
    return middleware
