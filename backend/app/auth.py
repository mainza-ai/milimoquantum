"""Milimo Quantum — Enterprise Authentication (Keycloak SSO).

Validates JWT access tokens against the Keycloak realm.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer
from keycloak import KeycloakOpenID
from keycloak.exceptions import KeycloakError

router = APIRouter(prefix="/api/auth", tags=["auth"])

logger = logging.getLogger(__name__)

# Keycloak configuration from environment
KC_SERVER_URL = os.environ.get("KC_SERVER_URL", "http://localhost:8080/")
KC_REALM_NAME = os.environ.get("KC_REALM_NAME", "milimo-realm")
KC_CLIENT_ID = os.environ.get("KC_CLIENT_ID", "milimo-client")
AUTH_ENABLED = os.environ.get("AUTH_ENABLED", "true").lower() == "true"

# OAuth2 scheme for Swagger UI
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{KC_SERVER_URL}realms/{KC_REALM_NAME}/protocol/openid-connect/token" if AUTH_ENABLED else "token",
    auto_error=False,
)

keycloak_openid = None
if AUTH_ENABLED:
    try:
        keycloak_openid = KeycloakOpenID(
            server_url=KC_SERVER_URL,
            client_id=KC_CLIENT_ID,
            realm_name=KC_REALM_NAME,
            verify=True,
        )
    except Exception as e:
        logger.error(f"Failed to initialize Keycloak client: {e}")


async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> dict:
    """Validate token and return current user."""
    # If auth is disabled, raise an error instead of using a mock user
    if not AUTH_ENABLED:
        logger.warning("AUTH_ENABLED is false, but dev-user-id fallback has been removed for security.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required but disabled in the configuration.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Missing Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not keycloak_openid:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is currently unavailable",
        )

    try:
        from jose import jwt as jose_jwt

        # Get public key for signature validation from Keycloak
        public_key = (
            "-----BEGIN PUBLIC KEY-----\n" 
            + keycloak_openid.public_key() 
            + "\n-----END PUBLIC KEY-----"
        )
        
        # Decode the JWT directly with python-jose (avoids keycloak lib version issue)
        token_info = jose_jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            options={
                "verify_aud": False,
                "verify_at_hash": False,
                "leeway": 3600 # 1 hour of clock drift/expiration leeway
            },
        )
        return token_info
        
    except KeycloakError as e:
        logger.warning(f"Invalid authentication token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        # Debug: Log unverified claims to see iat/exp
        try:
            unverified = jose_jwt.get_unverified_claims(token)
            logger.error(f"Authentication error ({type(e).__name__}): {e}. Claims: exp={unverified.get('exp')}, iat={unverified.get('iat')}")
        except:
            logger.error(f"Authentication error ({type(e).__name__}): {e}")
            
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Session expired or invalid",
        )


def require_role(role_name: str):
    """Dependency constructor to require a specific Keycloak role."""
    async def role_checker(user: dict = Depends(get_current_user)):
        roles = user.get("realm_access", {}).get("roles", [])
        if role_name not in roles and AUTH_ENABLED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires role: {role_name}",
            )
        return user
    return role_checker

@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    return {"user": user}
