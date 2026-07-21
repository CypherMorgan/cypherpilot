"""User repository — data access for the users table."""

from __future__ import annotations

from sqlalchemy import select

from app.infrastructure.repository import BaseRepository
from app.modules.auth.models import User


class UserRepository(BaseRepository[User]):
    """Repository for User model."""

    model_class = User

    async def get_by_username(self, username: str) -> User | None:
        """Find a user by username (case-insensitive)."""
        stmt = select(self.model_class).where(
            self.model_class.username == username
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def get_by_email(self, email: str) -> User | None:
        """Find a user by email (case-insensitive)."""
        stmt = select(self.model_class).where(
            self.model_class.email == email
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def get_by_username_or_email(self, identifier: str) -> User | None:
        """Find a user by username or email.

        Tries username first, then email.  Useful for login where the
        user might enter either.
        """
        user = await self.get_by_username(identifier)
        if user is not None:
            return user
        return await self.get_by_email(identifier)

    async def username_exists(self, username: str) -> bool:
        """Check if a username is already taken."""
        return await self.get_by_username(username) is not None

    async def email_exists(self, email: str) -> bool:
        """Check if an email is already registered."""
        return await self.get_by_email(email) is not None
