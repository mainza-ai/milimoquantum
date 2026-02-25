"""Milimo Quantum — Authorization & Roles.

Role-based access control (RBAC) definitions and decorators.
"""
from __future__ import annotations

import functools
from enum import Enum
from typing import List, Optional

from fastapi import HTTPException, Header


class Role(str, Enum):
    ADMIN = "admin"
    RESEARCHER = "researcher"
    ANALYST = "analyst"
    VIEWER = "viewer"


class User:
    def __init__(self, username: str, roles: List[Role]):
        self.username = username
        self.roles = roles

    def has_role(self, role: Role) -> bool:
        if Role.ADMIN in self.roles:
            return True  # Admin has all permissions
        return role in self.roles


# Mock user database
USERS = {
    "admin": User("admin", [Role.ADMIN]),
    "alice": User("alice", [Role.RESEARCHER]),
    "bob": User("bob", [Role.ANALYST, Role.VIEWER]),
}


def require_role(role: Role):
    """Decorator to enforce role-based access control."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # In production, get user from JWT token header
            # Here we mock it via 'X-User' header for demo
            username = kwargs.get("x_user", "admin") # Default to admin for easier testing
            
            user = USERS.get(username)
            if not user:
                 # Auto-create guest for simplicity in dev
                 user = User(username, [Role.RESEARCHER])

            if not user.has_role(role):
                raise HTTPException(
                    status_code=403, 
                    detail=f"Permission denied. Required role: {role.value}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
