"""Tests for AuthService — password hashing, JWT, register, login."""

from __future__ import annotations

import uuid

import jwt
import pytest

from app.modules.auth.config import AuthConfig
from app.modules.auth.schemas import RegisterRequest
from app.modules.auth.service import AuthService


class TestPasswordHashing:
    """Tests for bcrypt password hashing."""

    def test_hash_password(self) -> None:
        hashed = AuthService.hash_password("mypassword")
        assert hashed != "mypassword"
        assert len(hashed) > 0

    def test_verify_password_correct(self) -> None:
        hashed = AuthService.hash_password("correct-password")
        assert AuthService.verify_password("correct-password", hashed) is True

    def test_verify_password_wrong(self) -> None:
        hashed = AuthService.hash_password("correct-password")
        assert AuthService.verify_password("wrong-password", hashed) is False

    def test_different_hashes(self) -> None:
        h1 = AuthService.hash_password("same-password")
        h2 = AuthService.hash_password("same-password")
        # bcrypt uses random salt, so hashes should differ
        assert h1 != h2


class TestJWTTokens:
    """Tests for JWT token creation and verification."""

    def test_create_token(self, auth_service: AuthService) -> None:
        token = auth_service.create_access_token(
            user_id="test-user-id",
            role="user",
        )
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_token(self, auth_service: AuthService) -> None:
        token = auth_service.create_access_token(
            user_id="test-user-id",
            role="admin",
        )
        payload = auth_service.decode_access_token(token)
        assert payload["sub"] == "test-user-id"
        assert payload["role"] == "admin"
        assert "exp" in payload
        assert "iat" in payload

    def test_decode_invalid_token(self, auth_service: AuthService) -> None:
        with pytest.raises(jwt.InvalidTokenError):
            auth_service.decode_access_token("invalid.token.here")

    def test_decode_wrong_secret(self) -> None:
        config = AuthConfig(secret_key="wrong-secret")
        service = AuthService.__new__(AuthService)
        service._config = config

        # Create with one secret, decode with another
        token = jwt.encode(
            {"sub": "user", "role": "user"},
            "correct-secret",
            algorithm="HS256",
        )
        with pytest.raises(jwt.InvalidTokenError):
            service.decode_access_token(token)


class TestRegister:
    """Tests for user registration."""

    @pytest.mark.asyncio
    async def test_register_success(
        self, auth_service: AuthService
    ) -> None:
        data = RegisterRequest(
            username="newuser",
            email="new@example.com",
            password="password123",
        )
        result = await auth_service.register(data)

        assert result.access_token is not None
        assert result.user.username == "newuser"
        assert result.user.email == "new@example.com"
        assert result.user.role == "user"
        assert result.user.is_active is True

    @pytest.mark.asyncio
    async def test_register_duplicate_username(
        self, auth_service: AuthService
    ) -> None:
        data = RegisterRequest(
            username="duplicate",
            email="first@example.com",
            password="password123",
        )
        await auth_service.register(data)

        data2 = RegisterRequest(
            username="duplicate",
            email="second@example.com",
            password="password123",
        )
        with pytest.raises(ValueError, match="already taken"):
            await auth_service.register(data2)

    @pytest.mark.asyncio
    async def test_register_duplicate_email(
        self, auth_service: AuthService
    ) -> None:
        data = RegisterRequest(
            username="user1",
            email="same@example.com",
            password="password123",
        )
        await auth_service.register(data)

        data2 = RegisterRequest(
            username="user2",
            email="same@example.com",
            password="password123",
        )
        with pytest.raises(ValueError, match="already registered"):
            await auth_service.register(data2)


class TestLogin:
    """Tests for user login."""

    @pytest.mark.asyncio
    async def test_login_success(
        self, auth_service: AuthService
    ) -> None:
        # Register first
        reg_data = RegisterRequest(
            username="logintest",
            email="login@example.com",
            password="mypassword",
        )
        await auth_service.register(reg_data)

        # Login
        result = await auth_service.login("logintest", "mypassword")
        assert result.access_token is not None
        assert result.user.username == "logintest"

    @pytest.mark.asyncio
    async def test_login_wrong_password(
        self, auth_service: AuthService
    ) -> None:
        reg_data = RegisterRequest(
            username="logintest2",
            email="login2@example.com",
            password="mypassword",
        )
        await auth_service.register(reg_data)

        with pytest.raises(ValueError, match="Invalid"):
            await auth_service.login("logintest2", "wrongpassword")

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(
        self, auth_service: AuthService
    ) -> None:
        with pytest.raises(ValueError, match="Invalid"):
            await auth_service.login("nobody", "password")

    @pytest.mark.asyncio
    async def test_login_by_email(
        self, auth_service: AuthService
    ) -> None:
        reg_data = RegisterRequest(
            username="emaillogin",
            email="emaillogin@example.com",
            password="mypassword",
        )
        await auth_service.register(reg_data)

        result = await auth_service.login("emaillogin@example.com", "mypassword")
        assert result.user.username == "emaillogin"

    @pytest.mark.asyncio
    async def test_login_deactivated_user(
        self, auth_service: AuthService
    ) -> None:
        reg_data = RegisterRequest(
            username="deactivated",
            email="deactivated@example.com",
            password="mypassword",
        )
        token_resp = await auth_service.register(reg_data)

        # Deactivate user
        user = await auth_service.get_user(token_resp.user.id)
        assert user is not None
        user.is_active = False
        await auth_service._session.commit()

        with pytest.raises(ValueError, match="deactivated"):
            await auth_service.login("deactivated", "mypassword")


class TestGetUser:
    """Tests for user retrieval."""

    @pytest.mark.asyncio
    async def test_get_user(
        self, auth_service: AuthService
    ) -> None:
        reg_data = RegisterRequest(
            username="gettest",
            email="get@example.com",
            password="password123",
        )
        result = await auth_service.register(reg_data)

        user = await auth_service.get_user(result.user.id)
        assert user is not None
        assert user.username == "gettest"

    @pytest.mark.asyncio
    async def test_get_nonexistent_user(
        self, auth_service: AuthService
    ) -> None:
        user = await auth_service.get_user(uuid.uuid4())
        assert user is None
