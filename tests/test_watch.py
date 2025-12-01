import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta
from app.models.active_session import ActiveSession
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

class TestGetActivePlayers:
    """Test get active players endpoint"""
    
    async def test_get_active_players_empty(self, client: AsyncClient):
        """Test getting active players when none exist"""
        response = await client.get("/api/v1/watch/active")
        assert response.status_code == 200
        data = response.json()
        assert data["players"] == []
    
    async def test_get_active_players_with_sessions(
        self, client: AsyncClient, test_db: AsyncSession, test_user: User
    ):
        """Test getting active players with active sessions"""
        session = ActiveSession(
            user_id=test_user.id,
            username=test_user.username,
            game_mode="pass-through",
            game_state={
                "snake": [{"x": 10, "y": 10}],
                "food": {"x": 15, "y": 15},
                "direction": "right",
                "score": 10,
                "gameOver": False,
            },
            score=10,
            last_updated_at=datetime.utcnow(),
        )
        test_db.add(session)
        await test_db.commit()
        
        response = await client.get("/api/v1/watch/active")
        assert response.status_code == 200
        data = response.json()
        assert len(data["players"]) == 1
        assert data["players"][0]["username"] == test_user.username
        assert data["players"][0]["score"] == 10

class TestStartGame:
    """Test start game session endpoint"""
    
    async def test_start_game_success(
        self, authenticated_client: AsyncClient, test_user: User
    ):
        """Test successfully starting a game session"""
        response = await authenticated_client.post(
            "/api/v1/watch/start",
            json={"gameMode": "pass-through"}
        )
        assert response.status_code == 201
        data = response.json()
        assert "sessionId" in data
        assert data["gameMode"] == "pass-through"
        assert "startedAt" in data
    
    async def test_start_game_walls_mode(
        self, authenticated_client: AsyncClient, test_user: User
    ):
        """Test starting game in walls mode"""
        response = await authenticated_client.post(
            "/api/v1/watch/start",
            json={"gameMode": "walls"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["gameMode"] == "walls"
    
    async def test_start_game_no_auth(self, client: AsyncClient):
        """Test starting game without authentication"""
        response = await client.post(
            "/api/v1/watch/start",
            json={"gameMode": "pass-through"}
        )
        assert response.status_code == 401

class TestUpdateGame:
    """Test update game session endpoint"""
    
    async def test_update_game_success(
        self, authenticated_client: AsyncClient, test_db: AsyncSession, test_user: User
    ):
        """Test successfully updating game state"""
        # Create a session first
        session = ActiveSession(
            user_id=test_user.id,
            username=test_user.username,
            game_mode="pass-through",
            game_state={
                "snake": [{"x": 10, "y": 10}],
                "food": {"x": 15, "y": 15},
                "direction": "right",
                "score": 0,
                "gameOver": False,
            },
            score=0,
        )
        test_db.add(session)
        await test_db.commit()
        await test_db.refresh(session)
        
        response = await authenticated_client.put(
            f"/api/v1/watch/update/{session.id}",
            json={
                "gameState": {
                    "snake": [{"x": 11, "y": 10}, {"x": 10, "y": 10}],
                    "food": {"x": 15, "y": 15},
                    "direction": "right",
                    "score": 10,
                    "gameOver": False,
                }
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Game state updated"
        assert "lastUpdatedAt" in data
    
    async def test_update_game_not_found(self, authenticated_client: AsyncClient):
        """Test updating non-existent session"""
        response = await authenticated_client.put(
            "/api/v1/watch/update/nonexistent-id",
            json={
                "gameState": {
                    "snake": [{"x": 10, "y": 10}],
                    "food": {"x": 15, "y": 15},
                    "direction": "right",
                    "score": 0,
                    "gameOver": False,
                }
            }
        )
        assert response.status_code == 404
    
    async def test_update_game_wrong_user(
        self, authenticated_client: AsyncClient, test_db: AsyncSession, test_user: User
    ):
        """Test updating session belonging to another user"""
        # Create another user and session
        other_user = User(
            username="otheruser",
            email="other@example.com",
            password_hash="hash",
        )
        test_db.add(other_user)
        await test_db.commit()
        await test_db.refresh(other_user)
        
        session = ActiveSession(
            user_id=other_user.id,
            username=other_user.username,
            game_mode="pass-through",
            game_state={
                "snake": [{"x": 10, "y": 10}],
                "food": {"x": 15, "y": 15},
                "direction": "right",
                "score": 0,
                "gameOver": False,
            },
            score=0,
        )
        test_db.add(session)
        await test_db.commit()
        await test_db.refresh(session)
        
        response = await authenticated_client.put(
            f"/api/v1/watch/update/{session.id}",
            json={
                "gameState": {
                    "snake": [{"x": 10, "y": 10}],
                    "food": {"x": 15, "y": 15},
                    "direction": "right",
                    "score": 0,
                    "gameOver": False,
                }
            }
        )
        assert response.status_code == 403

class TestEndGame:
    """Test end game session endpoint"""
    
    async def test_end_game_success(
        self, authenticated_client: AsyncClient, test_db: AsyncSession, test_user: User
    ):
        """Test successfully ending a game session"""
        # Create a session first
        session = ActiveSession(
            user_id=test_user.id,
            username=test_user.username,
            game_mode="pass-through",
            game_state={
                "snake": [{"x": 10, "y": 10}],
                "food": {"x": 15, "y": 15},
                "direction": "right",
                "score": 150,
                "gameOver": True,
            },
            score=150,
        )
        test_db.add(session)
        await test_db.commit()
        await test_db.refresh(session)
        
        response = await authenticated_client.post(
            f"/api/v1/watch/end/{session.id}",
            json={
                "finalScore": 150,
                "gameMode": "pass-through"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Session ended"
        assert "leaderboardEntry" in data
        assert data["leaderboardEntry"]["score"] == 150
        
        # Verify session was deleted
        result = await test_db.execute(
            select(ActiveSession).filter(ActiveSession.id == session.id)
        )
        deleted_session = result.scalar_one_or_none()
        assert deleted_session is None
    
    async def test_end_game_not_found(self, authenticated_client: AsyncClient):
        """Test ending non-existent session"""
        response = await authenticated_client.post(
            "/api/v1/watch/end/nonexistent-id",
            json={
                "finalScore": 100,
                "gameMode": "pass-through"
            }
        )
        assert response.status_code == 404
    
    async def test_end_game_wrong_user(
        self, authenticated_client: AsyncClient, test_db: AsyncSession, test_user: User
    ):
        """Test ending session belonging to another user"""
        # Create another user and session
        other_user = User(
            username="otheruser",
            email="other@example.com",
            password_hash="hash",
        )
        test_db.add(other_user)
        await test_db.commit()
        await test_db.refresh(other_user)
        
        session = ActiveSession(
            user_id=other_user.id,
            username=other_user.username,
            game_mode="pass-through",
            game_state={
                "snake": [{"x": 10, "y": 10}],
                "food": {"x": 15, "y": 15},
                "direction": "right",
                "score": 100,
                "gameOver": True,
            },
            score=100,
        )
        test_db.add(session)
        await test_db.commit()
        await test_db.refresh(session)
        
        response = await authenticated_client.post(
            f"/api/v1/watch/end/{session.id}",
            json={
                "finalScore": 100,
                "gameMode": "pass-through"
            }
        )
        assert response.status_code == 403

class TestGetActivePlayer:
    """Test get specific active player endpoint"""
    
    async def test_get_active_player_success(
        self, client: AsyncClient, test_db: AsyncSession, test_user: User
    ):
        """Test getting specific active player"""
        session = ActiveSession(
            user_id=test_user.id,
            username=test_user.username,
            game_mode="pass-through",
            game_state={
                "snake": [{"x": 10, "y": 10}],
                "food": {"x": 15, "y": 15},
                "direction": "right",
                "score": 50,
                "gameOver": False,
            },
            score=50,
            last_updated_at=datetime.utcnow(),
        )
        test_db.add(session)
        await test_db.commit()
        await test_db.refresh(session)
        
        response = await client.get(f"/api/v1/watch/active/{session.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == session.id
        assert data["username"] == test_user.username
        assert data["score"] == 50
    
    async def test_get_active_player_not_found(self, client: AsyncClient):
        """Test getting non-existent player"""
        response = await client.get("/api/v1/watch/active/nonexistent-id")
        assert response.status_code == 404

