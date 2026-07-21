"""Tests for Auth API endpoints.

Integration tests using the test HTTP client to verify
register, login, me, and change-password endpoints.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

API_BASE = "/api/v1/auth"


class TestRegisterEndpoint:
    """Tests for POST /auth/register."""

    @pytest.mark.asyncio
    async def test_register_success(
        self, client: AsyncClient
    ) -> None:
        resp = await client.post(
            f"{API_BASE}/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "password123",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert data["user"]["username"] == "testuser"
        assert data["user"]["email"] == "test@example.com"
        assert data["user"]["role"] == "user"
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_register_duplicate(
        self, client: AsyncClient
    ) -> None:
        payload = {
            "username": "dupuser",
            "email": "dup@example.com",
            "password": "password123",
        }
        resp1 = await client.post(f"{API_BASE}/register", json=payload)
        assert resp1.status_code == 201

        resp2 = await client.post(f"{API_BASE}/register", json=payload)
        assert resp2.status_code == 409

    @pytest.mark.asyncio
    async def test_register_invalid_email(
        self, client: AsyncClient
    ) -> None:
        resp = await client.post(
            f"{API_BASE}/register",
            json={
                "username": "bademail",
                "email": "not-an-email",
                "password": "password123",
            },
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_register_short_password(
        self, client: AsyncClient
    ) -> None:
        resp = await client.post(
            f"{API_BASE}/register",
            json={
                "username": "shortpw",
                "email": "short@example.com",
                "password": "123",
            },
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_register_short_username(
        self, client: AsyncClient
    ) -> None:
        resp = await client.post(
            f"{API_BASE}/register",
            json={
                "username": "ab",
                "email": "ab@example.com",
                "password": "password123",
            },
        )
        assert resp.status_code == 422


class TestLoginEndpoint:
    """Tests for POST /auth/login."""

    @pytest.mark.asyncio
    async def test_login_success(
        self, client: AsyncClient
    ) -> None:
        # Register first
        await client.post(
            f"{API_BASE}/register",
            json={
                "username": "loginuser",
                "email": "login@example.com",
                "password": "mypassword",
            },
        )

        # Login
        resp = await client.post(
            f"{API_BASE}/login",
            json={
                "username": "loginuser",
                "password": "mypassword",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["user"]["username"] == "loginuser"

    @pytest.mark.asyncio
    async def test_login_wrong_password(
        self, client: AsyncClient
    ) -> None:
        await client.post(
            f"{API_BASE}/register",
            json={
                "username": "wpuser",
                "email": "wp@example.com",
                 "password": "correct123",
            },
        )

        resp = await client.post(
            f"{API_BASE}/login",
            json={
                "username": "wpuser",
                "password": "wrong",
            },
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(
        self, client: AsyncClient
    ) -> None:
        resp = await client.post(
            f"{API_BASE}/login",
            json={
                "username": "ghost",
                "password": "password",
            },
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_login_by_email(
        self, client: AsyncClient
    ) -> None:
        await client.post(
            f"{API_BASE}/register",
            json={
                "username": "emailuser",
                "email": "emailuser@example.com",
                "password": "mypassword",
            },
        )

        resp = await client.post(
            f"{API_BASE}/login",
            json={
                "username": "emailuser@example.com",
                "password": "mypassword",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["user"]["username"] == "emailuser"


class TestMeEndpoint:
    """Tests for GET /auth/me."""

    @pytest.mark.asyncio
    async def test_me_authenticated(
        self, client: AsyncClient
    ) -> None:
        # Register
        reg_resp = await client.post(
            f"{API_BASE}/register",
            json={
                "username": "meuser",
                "email": "me@example.com",
                "password": "password123",
            },
        )
        token = reg_resp.json()["access_token"]

        # Get profile
        resp = await client.get(
            f"{API_BASE}/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["username"] == "meuser"

    @pytest.mark.asyncio
    async def test_me_unauthenticated(
        self, client: AsyncClient
    ) -> None:
        resp = await client.get(f"{API_BASE}/me")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_me_invalid_token(
        self, client: AsyncClient
    ) -> None:
        resp = await client.get(
            f"{API_BASE}/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert resp.status_code == 401


class TestChangePasswordEndpoint:
    """Tests for POST /auth/change-password."""

    @pytest.mark.asyncio
    async def test_change_password_success(
        self, client: AsyncClient
    ) -> None:
        # Register
        reg_resp = await client.post(
            f"{API_BASE}/register",
            json={
                "username": "chpwuser",
                "email": "chpw@example.com",
                "password": "oldpassword",
            },
        )
        token = reg_resp.json()["access_token"]

        # Change password
        resp = await client.post(
            f"{API_BASE}/change-password",
            json={
                "current_password": "oldpassword",
                "new_password": "newpassword123",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 204

        # Verify old password no longer works
        login_resp = await client.post(
            f"{API_BASE}/login",
            json={
                "username": "chpwuser",
                "password": "oldpassword",
            },
        )
        assert login_resp.status_code == 401

        # Verify new password works
        login_resp2 = await client.post(
            f"{API_BASE}/login",
            json={
                "username": "chpwuser",
                "password": "newpassword123",
            },
        )
        assert login_resp2.status_code == 200

    @pytest.mark.asyncio
    async def test_change_password_wrong_current(
        self, client: AsyncClient
    ) -> None:
        reg_resp = await client.post(
            f"{API_BASE}/register",
            json={
                "username": "cpwuser2",
                "email": "cpwuser2@example.com",
                "password": "correct123",
            },
        )
        assert reg_resp.status_code == 201, reg_resp.text
        token = reg_resp.json()["access_token"]

        resp = await client.post(
            f"{API_BASE}/change-password",
            json={
                "current_password": "wrong",
                "new_password": "newpassword123",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400
