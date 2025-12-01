import pytest
from httpx import AsyncClient
from datetime import date
from app.models.leaderboard import Leaderboard
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

class TestGetLeaderboard:
    """Test get leaderboard endpoint"""
    
    async def test_get_leaderboard_empty(self, client: AsyncClient):
        """Test getting leaderboard when empty"""
        response = await client.get("/api/v1/leaderboard")
        assert response.status_code == 200
        data = response.json()
        assert data["entries"] == []
        assert data["total"] == 0
        assert data["limit"] == 10
        assert data["offset"] == 0
    
    async def test_get_leaderboard_with_entries(
        self, client: AsyncClient, test_db: AsyncSession, test_user: User
    ):
        """Test getting leaderboard with entries"""
        # Create some leaderboard entries
        entry1 = Leaderboard(
            user_id=test_user.id,
            username=test_user.username,
            score=100,
            game_mode="pass-through",
            date=date.today(),
        )
        entry2 = Leaderboard(
            user_id=test_user.id,
            username=test_user.username,
            score=200,
            game_mode="pass-through",
            date=date.today(),
        )
        test_db.add(entry1)
        test_db.add(entry2)
        await test_db.commit()
        
        response = await client.get("/api/v1/leaderboard")
        assert response.status_code == 200
        data = response.json()
        assert len(data["entries"]) == 2
        assert data["total"] == 2
        # Should be sorted by score descending
        assert data["entries"][0]["score"] == 200
        assert data["entries"][1]["score"] == 100
    
    async def test_get_leaderboard_with_limit(
        self, client: AsyncClient, test_db: AsyncSession, test_user: User
    ):
        """Test getting leaderboard with limit"""
        # Create multiple entries
        for i in range(15):
            entry = Leaderboard(
                user_id=test_user.id,
                username=test_user.username,
                score=100 + i,
                game_mode="pass-through",
                date=date.today(),
            )
            test_db.add(entry)
        await test_db.commit()
        
        response = await client.get("/api/v1/leaderboard?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["entries"]) == 5
        assert data["limit"] == 5
    
    async def test_get_leaderboard_with_offset(
        self, client: AsyncClient, test_db: AsyncSession, test_user: User
    ):
        """Test getting leaderboard with offset"""
        # Create multiple entries
        for i in range(10):
            entry = Leaderboard(
                user_id=test_user.id,
                username=test_user.username,
                score=100 + i,
                game_mode="pass-through",
                date=date.today(),
            )
            test_db.add(entry)
        await test_db.commit()
        
        response = await client.get("/api/v1/leaderboard?limit=5&offset=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["entries"]) == 5
        assert data["offset"] == 5
    
    async def test_get_leaderboard_filter_by_game_mode(
        self, client: AsyncClient, test_db: AsyncSession, test_user: User
    ):
        """Test filtering leaderboard by game mode"""
        entry1 = Leaderboard(
            user_id=test_user.id,
            username=test_user.username,
            score=100,
            game_mode="pass-through",
            date=date.today(),
        )
        entry2 = Leaderboard(
            user_id=test_user.id,
            username=test_user.username,
            score=200,
            game_mode="walls",
            date=date.today(),
        )
        test_db.add(entry1)
        test_db.add(entry2)
        await test_db.commit()
        
        response = await client.get("/api/v1/leaderboard?gameMode=pass-through")
        assert response.status_code == 200
        data = response.json()
        assert len(data["entries"]) == 1
        assert data["entries"][0]["game_mode"] == "pass-through"
    
    async def test_get_leaderboard_invalid_game_mode(self, client: AsyncClient):
        """Test filtering with invalid game mode"""
        response = await client.get("/api/v1/leaderboard?gameMode=invalid")
        assert response.status_code == 400

class TestSubmitScore:
    """Test submit score endpoint"""
    
    async def test_submit_score_success(
        self, authenticated_client: AsyncClient, test_user: User
    ):
        """Test successful score submission"""
        response = await authenticated_client.post(
            "/api/v1/leaderboard",
            json={
                "score": 150,
                "game_mode": "pass-through"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["score"] == 150
        assert data["game_mode"] == "pass-through"
        assert data["username"] == test_user.username
        assert "id" in data
        assert "date" in data
    
    async def test_submit_score_walls_mode(
        self, authenticated_client: AsyncClient, test_user: User
    ):
        """Test submitting score for walls mode"""
        response = await authenticated_client.post(
            "/api/v1/leaderboard",
            json={
                "score": 200,
                "game_mode": "walls"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["game_mode"] == "walls"
    
    async def test_submit_score_negative(self, authenticated_client: AsyncClient):
        """Test submitting negative score"""
        response = await authenticated_client.post(
            "/api/v1/leaderboard",
            json={
                "score": -10,
                "game_mode": "pass-through"
            }
        )
        assert response.status_code == 422
    
    async def test_submit_score_invalid_game_mode(self, authenticated_client: AsyncClient):
        """Test submitting score with invalid game mode"""
        response = await authenticated_client.post(
            "/api/v1/leaderboard",
            json={
                "score": 100,
                "game_mode": "invalid"
            }
        )
        assert response.status_code == 422
    
    async def test_submit_score_no_auth(self, client: AsyncClient):
        """Test submitting score without authentication"""
        response = await client.post(
            "/api/v1/leaderboard",
            json={
                "score": 100,
                "game_mode": "pass-through"
            }
        )
        assert response.status_code == 401

