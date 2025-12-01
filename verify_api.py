#!/usr/bin/env python3
"""
API Verification Script for Snake Game Backend

This script tests the API endpoints in sequence:
1. Register User
2. Login
3. Get Token
4. Start Game
5. Update Game
6. End Game
7. Check Leaderboard
8. Test WebSocket connection
"""

import asyncio
import httpx
import json
from typing import Optional

BASE_URL = "http://localhost:8000/api/v1"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(message: str):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_error(message: str):
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_info(message: str):
    print(f"{Colors.BLUE}ℹ {message}{Colors.END}")

def print_warning(message: str):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")

async def test_signup(client: httpx.AsyncClient) -> Optional[dict]:
    """Test user signup"""
    print_info("Testing POST /auth/signup...")
    
    signup_data = {
        "username": "testplayer",
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    try:
        response = await client.post(f"{BASE_URL}/auth/signup", json=signup_data)
        if response.status_code == 201:
            data = response.json()
            print_success(f"User created: {data['user']['username']}")
            return data
        else:
            print_error(f"Signup failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print_error(f"Signup error: {e}")
        return None

async def test_login(client: httpx.AsyncClient) -> Optional[dict]:
    """Test user login"""
    print_info("Testing POST /auth/login...")
    
    login_data = {
        "username": "testplayer",
        "password": "testpassword123"
    }
    
    try:
        response = await client.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Login successful: {data['user']['username']}")
            return data
        else:
            print_error(f"Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print_error(f"Login error: {e}")
        return None

async def test_get_me(client: httpx.AsyncClient, token: str) -> bool:
    """Test GET /auth/me"""
    print_info("Testing GET /auth/me...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = await client.get(f"{BASE_URL}/auth/me", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Current user: {data['username']}")
            return True
        else:
            print_error(f"Get me failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print_error(f"Get me error: {e}")
        return False

async def test_start_game(client: httpx.AsyncClient, token: str) -> Optional[str]:
    """Test POST /watch/start"""
    print_info("Testing POST /watch/start...")
    
    headers = {"Authorization": f"Bearer {token}"}
    start_data = {
        "gameMode": "pass-through"
    }
    
    try:
        response = await client.post(f"{BASE_URL}/watch/start", json=start_data, headers=headers)
        if response.status_code == 201:
            data = response.json()
            session_id = data["sessionId"]
            print_success(f"Game started: {session_id}")
            return session_id
        else:
            print_error(f"Start game failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print_error(f"Start game error: {e}")
        return None

async def test_update_game(client: httpx.AsyncClient, token: str, session_id: str) -> bool:
    """Test PUT /watch/update/:sessionId"""
    print_info("Testing PUT /watch/update/:sessionId...")
    
    headers = {"Authorization": f"Bearer {token}"}
    update_data = {
        "gameState": {
            "snake": [
                {"x": 5, "y": 5},
                {"x": 4, "y": 5},
                {"x": 3, "y": 5}
            ],
            "food": {"x": 10, "y": 10},
            "direction": "right",
            "score": 10,
            "gameOver": False
        }
    }
    
    try:
        response = await client.put(
            f"{BASE_URL}/watch/update/{session_id}",
            json=update_data,
            headers=headers
        )
        if response.status_code == 200:
            print_success("Game state updated")
            return True
        else:
            print_error(f"Update game failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print_error(f"Update game error: {e}")
        return False

async def test_end_game(client: httpx.AsyncClient, token: str, session_id: str) -> bool:
    """Test POST /watch/end/:sessionId"""
    print_info("Testing POST /watch/end/:sessionId...")
    
    headers = {"Authorization": f"Bearer {token}"}
    end_data = {
        "finalScore": 150,
        "gameMode": "pass-through"
    }
    
    try:
        response = await client.post(
            f"{BASE_URL}/watch/end/{session_id}",
            json=end_data,
            headers=headers
        )
        if response.status_code == 200:
            data = response.json()
            print_success(f"Game ended. Score submitted: {data['leaderboardEntry']['score']}")
            return True
        else:
            print_error(f"End game failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print_error(f"End game error: {e}")
        return False

async def test_get_leaderboard(client: httpx.AsyncClient) -> bool:
    """Test GET /leaderboard"""
    print_info("Testing GET /leaderboard...")
    
    try:
        response = await client.get(f"{BASE_URL}/leaderboard?limit=10")
        if response.status_code == 200:
            data = response.json()
            print_success(f"Leaderboard retrieved: {len(data['entries'])} entries")
            if data['entries']:
                top_entry = data['entries'][0]
                print_info(f"  Top score: {top_entry['username']} - {top_entry['score']}")
            return True
        else:
            print_error(f"Get leaderboard failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print_error(f"Get leaderboard error: {e}")
        return False

async def test_get_active_players(client: httpx.AsyncClient) -> bool:
    """Test GET /watch/active"""
    print_info("Testing GET /watch/active...")
    
    try:
        response = await client.get(f"{BASE_URL}/watch/active")
        if response.status_code == 200:
            data = response.json()
            print_success(f"Active players: {len(data['players'])}")
            return True
        else:
            print_error(f"Get active players failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print_error(f"Get active players error: {e}")
        return False

async def test_websocket():
    """Test WebSocket connection"""
    print_info("Testing WebSocket connection...")
    
    try:
        import websockets
        uri = "ws://localhost:8000/ws"
        
        async with websockets.connect(uri) as websocket:
            # Wait for connection message
            message = await websocket.recv()
            data = json.loads(message)
            if data.get("type") == "connected":
                print_success("WebSocket connected")
            
            # Send subscribe message
            await websocket.send(json.dumps({
                "type": "subscribe",
                "playerId": "test-id"
            }))
            
            # Send ping
            await websocket.send(json.dumps({"type": "ping"}))
            pong = await websocket.recv()
            if json.loads(pong).get("type") == "pong":
                print_success("WebSocket ping/pong working")
            
            return True
    except ImportError:
        print_warning("websockets library not installed. Skipping WebSocket test.")
        print_warning("Install with: pip install websockets")
        return None
    except Exception as e:
        print_error(f"WebSocket error: {e}")
        return False

async def main():
    """Run all API tests"""
    print("\n" + "="*60)
    print("Snake Game API Verification Script")
    print("="*60 + "\n")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test signup
        signup_result = await test_signup(client)
        if not signup_result:
            print_error("Signup failed. Cannot continue.")
            return
        
        token = signup_result["token"]
        
        # Test login
        login_result = await test_login(client)
        if not login_result:
            print_warning("Login failed, but continuing with signup token...")
        else:
            token = login_result["token"]
        
        # Test get me
        await test_get_me(client, token)
        
        # Test start game
        session_id = await test_start_game(client, token)
        if not session_id:
            print_error("Cannot continue without session ID")
            return
        
        # Test update game
        await test_update_game(client, token, session_id)
        
        # Test get active players
        await test_get_active_players(client)
        
        # Test end game
        await test_end_game(client, token, session_id)
        
        # Test leaderboard
        await test_get_leaderboard(client)
        
        # Test WebSocket
        await test_websocket()
    
    print("\n" + "="*60)
    print("Verification complete!")
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(main())

