# exceptions.py
from typing import Any, Dict, Optional
from fastapi import HTTPException, status
from datetime import datetime
from fastapi.responses import JSONResponse


class APIException(HTTPException):
    """Base API exception with structured error response"""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code


class NotFoundException(APIException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="NOT_FOUND"
        )


class ValidationException(APIException):
    def __init__(self, detail: str = "Validation error"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code="VALIDATION_ERROR"
        )


class UnauthorizedException(APIException):
    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="UNAUTHORIZED"
        )


class RateLimitException(APIException):
    def __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            error_code="RATE_LIMIT_EXCEEDED"
        )


async def global_exception_handler(request, exc):
    """Global exception handler for consistent error responses"""
    from logging_config import logger
    
    logger.error(
        "API Exception",
        exc_info=exc,
        path=request.url.path,
        method=request.method,
        status_code=exc.status_code
    )
    
    error_response = {
        "error": {
            "code": getattr(exc, "error_code", "INTERNAL_ERROR"),
            "message": str(exc.detail),
            "timestamp": datetime.now().isoformat()
        }
    }
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response,
        headers=getattr(exc, "headers", None)
    )