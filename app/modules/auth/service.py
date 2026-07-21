"""Authentication service — password hashing, JWT tokens, user management.

Uses bcrypt for password hashing and PyJWT for token creation.
All crypto is isolated here; the router and repository never touch
raw passwords or token signing directly.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.modules.auth.config import AuthConfig
from app.modules.auth.models import User, UserRole
from app.modules.auth.repository import UserRepository
from app.modules.auth.schemas import (
    RegisterRequest,
    TokenResponse,
    UserResponse,
)

_logger = get_logger(__name__)


class AuthService:
    """Encapsulates authentication logic.

    Parameters:
        session: Async database session.
        config: Auth configuration (secret key, token settings).
    """

    def __init__(self, session: AsyncSession, config: AuthConfig) -> None:
        self._session = session
        self._config = config
        self._repo = UserRepository(session)

    # ── Password hashing ────────────────────────────────────────

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a plaintext password with bcrypt."""
        return bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt(),
        ).decode("utf-8")

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify a plaintext password against a bcrypt hash."""
        return bcrypt.checkpw(
            password.encode("utf-8"),
            hashed.encode("utf-8"),
        )

    # ── JWT tokens ──────────────────────────────────────────────

    def create_access_token(
        self,
        user_id: str,
        role: str,
        extra_claims: dict[str, Any] | None = None,
    ) -> str:
        """Create a signed JWT access token.

        Payload includes:
          - sub: user ID (string)
          - role: user role
          - iat: issued at (now)
          - exp: expiration
        """
        now = datetime.now(UTC)
        payload: dict[str, Any] = {
            "sub": user_id,
            "role": role,
            "iat": now,
            "exp": now + timedelta(minutes=self._config.token_expire_minutes),
        }
        if extra_claims:
            payload.update(extra_claims)

        return jwt.encode(
            payload,
            self._config.secret_key,
            algorithm=self._config.token_algorithm,
        )

    def decode_access_token(self, token: str) -> dict[str, Any]:
        """Decode and verify a JWT access token.

        Returns the payload dict on success.
        Raises ``jwt.ExpiredSignatureError`` if the token has expired.
        Raises ``jwt.InvalidTokenError`` for any other token issue.
        """
        return jwt.decode(
            token,
            self._config.secret_key,
            algorithms=[self._config.token_algorithm],
        )

    # ── User operations ─────────────────────────────────────────

    async def register(self, data: RegisterRequest) -> TokenResponse:
        """Register a new user and return a JWT token.

        Raises ValueError if username or email is already taken.
        """
        # Check uniqueness
        if await self._repo.username_exists(data.username):
            raise ValueError(f"Username '{data.username}' is already taken")
        if await self._repo.email_exists(data.email):
            raise ValueError(f"Email '{data.email}' is already registered")

        # Create user
        user = User(
            username=data.username,
            email=data.email,
            display_name=data.display_name,
            hashed_password=self.hash_password(data.password),
            role=UserRole.USER,
            is_active=True,
        )
        user = await self._repo.create(user)

        _logger.info(
            "User registered",
            user_id=str(user.id),
            username=user.username,
        )

        # Issue token
        token = self.create_access_token(
            user_id=str(user.id),
            role=user.role.value,
        )

        return TokenResponse(
            access_token=token,
            user=UserResponse.model_validate(user),
        )

    async def login(
        self, username: str, password: str
    ) -> TokenResponse:
        """Authenticate a user and return a JWT token.

        Raises ValueError if credentials are invalid or account is
        deactivated.
        """
        user = await self._repo.get_by_username_or_email(username)
        if user is None:
            raise ValueError("Invalid username or password")

        if not self.verify_password(password, user.hashed_password):
            raise ValueError("Invalid username or password")

        if not user.is_active:
            raise ValueError(
                "Account is deactivated. Contact an administrator."
            )

        _logger.info(
            "User logged in",
            user_id=str(user.id),
            username=user.username,
        )

        token = self.create_access_token(
            user_id=str(user.id),
            role=user.role.value,
        )

        return TokenResponse(
            access_token=token,
            user=UserResponse.model_validate(user),
        )

    async def get_user(self, user_id: Any) -> User | None:
        """Retrieve a user by ID."""
        return await self._repo.get(user_id)

    async def get_user_response(self, user_id: Any) -> UserResponse | None:
        """Retrieve a user and return as a response schema."""
        user = await self.get_user(user_id)
        if user is None:
            return None
        return UserResponse.model_validate(user)
