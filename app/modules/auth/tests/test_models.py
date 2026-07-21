"""Tests for User and UserRole models."""

from __future__ import annotations

from app.modules.auth.models import User, UserRole


class TestUserRole:
    """Tests for the UserRole enum."""

    def test_role_values(self) -> None:
        assert UserRole.ADMIN.value == "admin"
        assert UserRole.USER.value == "user"
        assert UserRole.VIEWER.value == "viewer"

    def test_role_is_string(self) -> None:
        assert isinstance(UserRole.ADMIN, str)
        assert UserRole.ADMIN == "admin"


class TestUserModel:
    """Tests for the User ORM model."""

    def test_user_creation(self) -> None:
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed123",
            role=UserRole.USER,
            is_active=True,
        )
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == UserRole.USER
        assert user.is_active is True
        assert user.display_name is None

    def test_user_role_assignment(self) -> None:
        user = User(
            username="admin",
            email="admin@example.com",
            hashed_password="hashed",
            role=UserRole.ADMIN,
        )
        assert user.role == UserRole.ADMIN

    def test_user_tablename(self) -> None:
        assert User.__tablename__ == "users"
