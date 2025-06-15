"""
Authentication Utilities

This module provides utilities for password hashing and JWT token generation.
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from utils.logger import get_logger
from utils.config import get_config
from api.auth.models import UserInDB, TokenData, User

# Get logger
logger = get_logger()

# Password context for hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")

# Get JWT settings from config
SECRET_KEY = get_config("auth.secret_key", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
ALGORITHM = get_config("auth.algorithm", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = get_config("auth.access_token_expire_minutes", 30)
REFRESH_TOKEN_EXPIRE_DAYS = get_config("auth.refresh_token_expire_days", 7)

# Mock user database - in production, this would be a real database
fake_users_db = {
    "admin": {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "full_name": "Administrator",
        "disabled": False,
        "hashed_password": pwd_context.hash("Admin123!"),
        "roles": ["admin"]
    },
    "user": {
        "id": 2,
        "username": "user",
        "email": "user@example.com",
        "full_name": "Regular User",
        "disabled": False,
        "hashed_password": pwd_context.hash("User123!"),
        "roles": ["user"]
    }
}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password
        
    Returns:
        True if the password matches the hash, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hash a password
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    return pwd_context.hash(password)

def get_user(username: str) -> Optional[UserInDB]:
    """
    Get a user from the database
    
    Args:
        username: Username to look up
        
    Returns:
        User if found, None otherwise
    """
    if username in fake_users_db:
        user_dict = fake_users_db[username]
        return UserInDB(**user_dict)
    return None

def authenticate_user(username: str, password: str) -> Optional[User]:
    """
    Authenticate a user
    
    Args:
        username: Username to authenticate
        password: Password to verify
        
    Returns:
        User if authentication is successful, None otherwise
    """
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def create_token(data: Dict[str, Any], token_type: str = "access", expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT token (access or refresh)
    
    Args:
        data: Data to encode in the token
        token_type: Type of token ("access" or "refresh")
        expires_delta: Optional expiration time delta
        
    Returns:
        JWT token
    """
    to_encode = data.copy()
    
    # Set expiration based on token type
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        if token_type == "refresh":
            expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        else:  # access token
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "token_type": token_type})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token
    
    Args:
        data: Data to encode in the token
        expires_delta: Optional expiration time delta
        
    Returns:
        JWT token
    """
    return create_token(data, "access", expires_delta)

def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT refresh token
    
    Args:
        data: Data to encode in the token
        expires_delta: Optional expiration time delta
        
    Returns:
        JWT token
    """
    return create_token(data, "refresh", expires_delta)

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Get the current user from a JWT token
    
    Args:
        token: JWT token
        
    Returns:
        User if token is valid
        
    Raises:
        HTTPException: If token is invalid or user is not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        token_type: str = payload.get("token_type", "access")
        
        if username is None:
            raise credentials_exception
        
        # Ensure this is an access token, not a refresh token
        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Extract token data
        token_data = TokenData(
            username=username,
            roles=payload.get("roles", []),
            exp=payload.get("exp"),
            token_type=token_type
        )
    except JWTError:
        logger.error("JWT token validation error")
        raise credentials_exception
    
    # Get the user
    user = get_user(token_data.username)
    if user is None:
        logger.error(f"User not found: {token_data.username}")
        raise credentials_exception
    
    return user

def verify_refresh_token(refresh_token: str) -> Optional[TokenData]:
    """
    Verify a refresh token and extract its data
    
    Args:
        refresh_token: Refresh token to verify
        
    Returns:
        TokenData if token is valid, None otherwise
    """
    try:
        # Decode the token
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        token_type: str = payload.get("token_type", "access")
        
        # Ensure this is a refresh token
        if not username or token_type != "refresh":
            logger.warning("Invalid refresh token type")
            return None
        
        # Extract token data
        token_data = TokenData(
            username=username,
            roles=payload.get("roles", []),
            exp=payload.get("exp"),
            token_type=token_type
        )
        
        return token_data
    except JWTError as e:
        logger.error(f"Refresh token validation error: {str(e)}")
        return None

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get the current active user
    
    Args:
        current_user: Current user
        
    Returns:
        User if active
        
    Raises:
        HTTPException: If user is disabled
    """
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def check_admin_role(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Check if the current user has admin role
    
    Args:
        current_user: Current user
        
    Returns:
        User if has admin role
        
    Raises:
        HTTPException: If user does not have admin role
    """
    if "admin" not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    return current_user
