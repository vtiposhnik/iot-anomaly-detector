"""
Authentication Package

This package provides authentication functionality for the API.
"""
from api.auth.router import router
from api.auth.utils import get_current_active_user, check_admin_role

__all__ = ["router", "get_current_active_user", "check_admin_role"]
