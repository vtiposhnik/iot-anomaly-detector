"""
Authentication Router

This module provides API endpoints for authentication and user management.
"""
from datetime import timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from utils.logger import get_logger
from api.auth.models import User, UserCreate, UserUpdate, Token
from api.auth.utils import (
    authenticate_user, create_access_token, create_refresh_token, get_current_active_user,
    check_admin_role, get_user, get_password_hash, fake_users_db, verify_refresh_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

# Get logger
logger = get_logger()

# Create router
router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Get an access token and refresh token for authentication
    
    Args:
        form_data: OAuth2 form data with username and password
        
    Returns:
        Token with access token, refresh token and token type
        
    Raises:
        HTTPException: If authentication fails
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "roles": user.roles},
        expires_delta=access_token_expires
    )
    
    # Create refresh token
    refresh_token = create_refresh_token(
        data={"sub": user.username, "roles": user.roles}
    )
    
    logger.info(f"User {user.username} logged in")
    
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60  # in seconds
    }

@router.post("/refresh", response_model=Token)
async def refresh_access_token(refresh_token: str):
    """
    Get a new access token using a refresh token
    
    Args:
        refresh_token: Refresh token
        
    Returns:
        New access token and refresh token
        
    Raises:
        HTTPException: If refresh token is invalid
    """
    # Verify the refresh token
    token_data = verify_refresh_token(refresh_token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get the user
    user = get_user(token_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create new access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "roles": user.roles},
        expires_delta=access_token_expires
    )
    
    # Create new refresh token
    refresh_token = create_refresh_token(
        data={"sub": user.username, "roles": user.roles}
    )
    
    logger.info(f"User {user.username} refreshed token")
    
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60  # in seconds
    }

@router.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Get the current user
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current user information
    """
    return current_user

@router.get("/users", response_model=List[User])
async def read_users(current_user: User = Depends(check_admin_role)):
    """
    Get all users (admin only)
    
    Args:
        current_user: Current authenticated user with admin role
        
    Returns:
        List of all users
    """
    users = []
    for username, user_dict in fake_users_db.items():
        user = User(**user_dict)
        users.append(user)
    
    return users

@router.post("/users", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, current_user: User = Depends(check_admin_role)):
    """
    Create a new user (admin only)
    
    Args:
        user: User data to create
        current_user: Current authenticated user with admin role
        
    Returns:
        Created user
        
    Raises:
        HTTPException: If user already exists
    """
    if user.username in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Create user
    user_id = len(fake_users_db) + 1
    hashed_password = get_password_hash(user.password)
    
    user_dict = user.dict()
    user_dict.pop("password")
    user_dict["id"] = user_id
    user_dict["hashed_password"] = hashed_password
    user_dict["roles"] = ["user"]  # Default role
    
    fake_users_db[user.username] = user_dict
    
    logger.info(f"User {user.username} created by {current_user.username}")
    
    return User(**user_dict)

@router.put("/users/{username}", response_model=User)
async def update_user(
    username: str,
    user_update: UserUpdate,
    current_user: User = Depends(check_admin_role)
):
    """
    Update a user (admin only)
    
    Args:
        username: Username to update
        user_update: User data to update
        current_user: Current authenticated user with admin role
        
    Returns:
        Updated user
        
    Raises:
        HTTPException: If user does not exist
    """
    if username not in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update user
    user_dict = fake_users_db[username]
    update_data = user_update.dict(exclude_unset=True)
    
    if "password" in update_data:
        hashed_password = get_password_hash(update_data["password"])
        update_data["hashed_password"] = hashed_password
        del update_data["password"]
    
    for field, value in update_data.items():
        user_dict[field] = value
    
    fake_users_db[username] = user_dict
    
    logger.info(f"User {username} updated by {current_user.username}")
    
    return User(**user_dict)

@router.delete("/users/{username}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(username: str, current_user: User = Depends(check_admin_role)):
    """
    Delete a user (admin only)
    
    Args:
        username: Username to delete
        current_user: Current authenticated user with admin role
        
    Raises:
        HTTPException: If user does not exist or is the current user
    """
    if username not in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if username == current_user.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Delete user
    del fake_users_db[username]
    
    logger.info(f"User {username} deleted by {current_user.username}")
