import os
import jwt
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(auto_error=False)

def get_supabase_jwt_secret() -> str:
    """Retrieve the Supabase JWT secret from environment variables."""
    return os.getenv("SUPABASE_JWT_SECRET", "").strip()

def is_auth_disabled() -> bool:
    """Check if authentication is explicitly disabled for local offline testing."""
    app_env = os.getenv("APP_ENV", "development").lower()
    if app_env in ("production", "prod"):
        # 운영 환경에서는 DISABLE_AUTH 설정이 있어도 절대 비활성화하지 않음 (보안 안전망)
        return False
    disable_auth = os.getenv("DISABLE_AUTH", "").lower() in ("true", "1", "yes")
    return disable_auth

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Dict[str, Any]:
    """
    FastAPI dependency to authenticate and extract the Supabase user from JWT.
    
    1. Only in non-production local development with DISABLE_AUTH explicitly enabled, returns a mock user.
    2. Otherwise, strictly verifies the JWT token signature using HS256, expiration, and SUPABASE_JWT_SECRET.
    """
    jwt_secret = get_supabase_jwt_secret()
    auth_disabled = is_auth_disabled()
    app_env = os.getenv("APP_ENV", "development").lower()
    is_dev = app_env in ("development", "dev", "local")

    # Local development explicit fallback
    if is_dev and auth_disabled:
        return {
            "id": "dev-user-0001",
            "email": "developer@localhost.local",
            "role": "authenticated",
            "is_dev": True,
        }

    # If secret is missing, fail fast with a 500 configuration error
    if not jwt_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server authentication configuration error: SUPABASE_JWT_SECRET is missing."
        )

    # Token must be provided
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Missing Bearer token in Authorization header.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials.strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is empty.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Decode and strictly verify JWT
        # algorithms=["HS256"] and options prevent algorithm confusion attacks
        payload = jwt.decode(
            token,
            jwt_secret,
            algorithms=["HS256"],
            options={
                "verify_signature": True,
                "verify_alg": True,
                "verify_exp": True,
                "require": ["exp", "sub"],
                "verify_aud": False,  # Supabase payload may contain aud='authenticated'
            }
        )

        user_id = payload.get("sub") or payload.get("id")
        email = payload.get("email")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload: User ID missing.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return {
            "id": str(user_id),
            "email": email,
            "role": payload.get("role", "authenticated"),
            "app_metadata": payload.get("app_metadata", {}),
            "user_metadata": payload.get("user_metadata", {}),
        }

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )
