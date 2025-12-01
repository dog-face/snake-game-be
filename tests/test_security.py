import pytest
from app.core import security

class TestPasswordHashing:
    """Test password hashing and verification"""
    
    def test_hash_password(self):
        """Test password hashing"""
        password = "testpassword123"
        hashed = security.get_password_hash(password)
        assert hashed != password
        assert len(hashed) > 0
    
    def test_verify_password_correct(self):
        """Test verifying correct password"""
        password = "testpassword123"
        hashed = security.get_password_hash(password)
        assert security.verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test verifying incorrect password"""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = security.get_password_hash(password)
        assert security.verify_password(wrong_password, hashed) is False
    
    def test_hash_different_passwords_different_hashes(self):
        """Test that different passwords produce different hashes"""
        password1 = "password1"
        password2 = "password2"
        hashed1 = security.get_password_hash(password1)
        hashed2 = security.get_password_hash(password2)
        assert hashed1 != hashed2

class TestJWT:
    """Test JWT token creation and validation"""
    
    def test_create_access_token(self):
        """Test creating access token"""
        user_id = "test-user-id"
        token = security.create_access_token(user_id)
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_access_token_with_expiry(self):
        """Test creating access token with custom expiry"""
        from datetime import timedelta
        user_id = "test-user-id"
        expires_delta = timedelta(minutes=30)
        token = security.create_access_token(user_id, expires_delta=expires_delta)
        assert token is not None
    
    def test_decode_access_token(self):
        """Test decoding access token"""
        from jose import jwt
        from app.core.config import settings
        
        user_id = "test-user-id"
        token = security.create_access_token(user_id)
        
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        assert payload["sub"] == user_id
        assert "exp" in payload

