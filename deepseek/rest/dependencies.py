# dependencies.py
from typing import Optional
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from config import settings
from exceptions import UnauthorizedException


security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """Dependency to get current authenticated user"""
    if credentials is None:
        raise UnauthorizedException("Authentication required")
    
    try:
        token = credentials.credentials
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise UnauthorizedException("Invalid token")
        return {"id": user_id, "token": token}
    except jwt.ExpiredSignatureError:
        raise UnauthorizedException("Token has expired")
    except jwt.JWTError:
        raise UnauthorizedException("Invalid token")


def rate_limit(request: Request):
    """Simple rate limiting dependency"""
    # In production, use Redis or similar for distributed rate limiting
    from datetime import datetime
    from exceptions import RateLimitException
    
    client_ip = request.client.host
    path = request.url.path
    
    # This is a simplified version - implement proper rate limiting in production
    # using Redis, Memcached, or a dedicated rate limiting service
    request.state.rate_limit_key = f"rate_limit:{client_ip}:{path}"
    
    # For production, implement actual rate limiting logic here
    # Example: check Redis for request count in the last minute
    
    return True


# Common dependencies for endpoints
common_deps = [Depends(rate_limit)]