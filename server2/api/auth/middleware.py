"""
Authentication Middleware

This module provides middleware for handling authentication at the application level.
"""
from typing import List, Optional, Callable
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware

from utils.logger import get_logger
from utils.config import get_config
from api.auth.utils import SECRET_KEY, ALGORITHM

# Get logger
logger = get_logger()

class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware for handling authentication at the application level"""
    
    def __init__(self, app, public_endpoints: Optional[List[str]] = None):
        """
        Initialize the middleware
        
        Args:
            app: FastAPI application
            public_endpoints: List of endpoints that don't require authentication
        """
        super().__init__(app)
        self.public_endpoints = public_endpoints or []
        
        # Add public endpoints from config
        config_endpoints = get_config("auth.public_endpoints", [])
        self.public_endpoints.extend(config_endpoints)
        
        # Get auth enabled setting
        self.auth_enabled = get_config("auth.enabled", True)
        
        logger.info(f"Authentication middleware initialized with {len(self.public_endpoints)} public endpoints")
        logger.info(f"Authentication enabled: {self.auth_enabled}")
    
    async def dispatch(self, request: Request, call_next: Callable):
        """
        Dispatch the request
        
        Args:
            request: FastAPI request
            call_next: Next middleware or endpoint
            
        Returns:
            Response
        """
        # If authentication is disabled, skip middleware
        if not self.auth_enabled:
            return await call_next(request)
        
        # Check if the endpoint is public
        path = request.url.path
        if self._is_public_endpoint(path):
            return await call_next(request)
        
        # Check for token
        token = self._get_token_from_request(request)
        if not token:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Not authenticated"},
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Validate token
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
            
            if username is None:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid token"},
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Add user info to request state
            request.state.user = {
                "username": username,
                "roles": payload.get("roles", [])
            }
        
        except JWTError:
            logger.error("JWT token validation error")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid token"},
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Continue with the request
        return await call_next(request)
    
    def _is_public_endpoint(self, path: str) -> bool:
        """
        Check if the endpoint is public
        
        Args:
            path: Request path
            
        Returns:
            True if the endpoint is public, False otherwise
        """
        # Check exact matches
        if path in self.public_endpoints:
            return True
        
        # Check prefix matches (e.g. /docs/*)
        for endpoint in self.public_endpoints:
            if endpoint.endswith("*") and path.startswith(endpoint[:-1]):
                return True
        
        return False
    
    def _get_token_from_request(self, request: Request) -> Optional[str]:
        """
        Get the token from the request
        
        Args:
            request: FastAPI request
            
        Returns:
            Token if found, None otherwise
        """
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None
        
        # Check if it's a Bearer token
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None
        
        return parts[1]
