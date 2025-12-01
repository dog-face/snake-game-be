import pytest
from httpx import AsyncClient
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

class TestSignup:
    """Test user signup endpoint"""
    
    async def test_signup_success(self, client: AsyncClient, test_db: AsyncSession):
        """Test successful user signup"""
        response = await client.post(
            "/api/v1/auth/signup",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert "user" in data
        assert "token" in data
        assert data["user"]["username"] == "newuser"
        assert data["user"]["email"] == "newuser@example.com"
        assert "id" in data["user"]
    
    async def test_signup_duplicate_email(self, client: AsyncClient, test_user: User):
        """Test signup with duplicate email"""
        response = await client.post(
            "/api/v1/auth/signup",
            json={
                "username": "differentuser",
                "email": test_user.email,
                "password": "password123"
            }
        )
        assert response.status_code == 409
        data = response.json()
        assert "error" in data["detail"]
        assert data["detail"]["error"]["code"] == "EMAIL_EXISTS"
    
    async def test_signup_duplicate_username(self, client: AsyncClient, test_user: User):
        """Test signup with duplicate username"""
        response = await client.post(
            "/api/v1/auth/signup",
            json={
                "username": test_user.username,
                "email": "different@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 409
        data = response.json()
        assert "error" in data["detail"]
        assert data["detail"]["error"]["code"] == "USERNAME_EXISTS"
    
    async def test_signup_invalid_username_short(self, client: AsyncClient):
        """Test signup with username too short"""
        response = await client.post(
            "/api/v1/auth/signup",
            json={
                "username": "ab",
                "email": "test@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 422
    
    async def test_signup_invalid_username_long(self, client: AsyncClient):
        """Test signup with username too long"""
        response = await client.post(
            "/api/v1/auth/signup",
            json={
                "username": "a" * 21,
                "email": "test@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 422
    
    async def test_signup_invalid_username_characters(self, client: AsyncClient):
        """Test signup with invalid username characters"""
        response = await client.post(
            "/api/v1/auth/signup",
            json={
                "username": "user-name!",
                "email": "test@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 422
    
    async def test_signup_invalid_password_short(self, client: AsyncClient):
        """Test signup with password too short"""
        response = await client.post(
            "/api/v1/auth/signup",
            json={
                "username": "newuser",
                "email": "test@example.com",
                "password": "short"
            }
        )
        assert response.status_code == 422
    
    async def test_signup_invalid_email(self, client: AsyncClient):
        """Test signup with invalid email"""
        response = await client.post(
            "/api/v1/auth/signup",
            json={
                "username": "newuser",
                "email": "notanemail",
                "password": "password123"
            }
        )
        assert response.status_code == 422

class TestLogin:
    """Test user login endpoint"""
    
    async def test_login_success(self, client: AsyncClient, test_user: User):
        """Test successful login"""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": test_user.username,
                "password": "testpassword123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert "token" in data
        assert data["user"]["username"] == test_user.username
    
    async def test_login_invalid_username(self, client: AsyncClient):
        """Test login with invalid username"""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": "nonexistent",
                "password": "password123"
            }
        )
        assert response.status_code == 401
        data = response.json()
        assert "error" in data["detail"]
        assert data["detail"]["error"]["code"] == "INVALID_CREDENTIALS"
    
    async def test_login_invalid_password(self, client: AsyncClient, test_user: User):
        """Test login with invalid password"""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": test_user.username,
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
        data = response.json()
        assert "error" in data["detail"]
        assert data["detail"]["error"]["code"] == "INVALID_CREDENTIALS"

class TestGetMe:
    """Test get current user endpoint"""
    
    async def test_get_me_success(self, authenticated_client: AsyncClient, test_user: User):
        """Test getting current user with valid token"""
        response = await authenticated_client.get("/api/v1/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_user.username
        assert data["email"] == test_user.email
        assert data["id"] == test_user.id
    
    async def test_get_me_no_token(self, client: AsyncClient):
        """Test getting current user without token"""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401
    
    async def test_get_me_invalid_token(self, client: AsyncClient):
        """Test getting current user with invalid token"""
        client.headers.update({"Authorization": "Bearer invalid_token"})
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

class TestLogout:
    """Test logout endpoint"""
    
    async def test_logout_success(self, authenticated_client: AsyncClient):
        """Test successful logout"""
        response = await authenticated_client.post("/api/v1/auth/logout")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Logged out successfully"

