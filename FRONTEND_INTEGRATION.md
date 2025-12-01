# Frontend Integration Guide

## Overview

The Snake Game backend API is now fully implemented and ready for integration. This guide will help you replace the mock API service with real API calls.

## Quick Start

### Base URL
- **Development**: `http://localhost:8000/api/v1`
- **Production**: Update to your production URL when deployed

### API Documentation
- **Swagger UI**: http://localhost:8000/docs (interactive API explorer)
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Spec**: http://localhost:8000/openapi.json

## Authentication Flow

### 1. Signup
```typescript
POST /api/v1/auth/signup
Content-Type: application/json

{
  "username": "player1",
  "email": "player1@example.com",
  "password": "securePassword123"
}

Response (201):
{
  "user": {
    "id": "uuid",
    "username": "player1",
    "email": "player1@example.com",
    "createdAt": "2024-01-15T10:00:00Z",
    "updatedAt": "2024-01-15T10:00:00Z"
  },
  "token": "jwt_token_here"
}
```

### 2. Login
```typescript
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "player1",
  "password": "securePassword123"
}

Response (200):
{
  "user": { ... },
  "token": "jwt_token_here"
}
```

### 3. Using the Token
Include the JWT token in the `Authorization` header for all protected endpoints:
```
Authorization: Bearer <token>
```

### 4. Get Current User
```typescript
GET /api/v1/auth/me
Authorization: Bearer <token>

Response (200):
{
  "id": "uuid",
  "username": "player1",
  "email": "player1@example.com",
  "createdAt": "2024-01-15T10:00:00Z",
  "updatedAt": "2024-01-15T10:00:00Z"
}
```

## Updating Your API Service

### Update `src/services/api.ts`

Replace the mock implementation with real API calls:

```typescript
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

class ApiService {
  private token: string | null = null;

  // Store token after login/signup
  setToken(token: string) {
    this.token = token;
    localStorage.setItem('token', token);
  }

  // Get token from storage
  getToken(): string | null {
    if (!this.token) {
      this.token = localStorage.getItem('token');
    }
    return this.token;
  }

  // Clear token on logout
  clearToken() {
    this.token = null;
    localStorage.removeItem('token');
  }

  // Helper to get auth headers
  private getAuthHeaders(): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };
    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  }

  // Authentication
  async login(credentials: LoginCredentials): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail?.error?.message || 'Login failed');
    }

    const data = await response.json();
    this.setToken(data.token);
    return data.user;
  }

  async signup(data: SignupData): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail?.error?.message || 'Signup failed');
    }

    const result = await response.json();
    this.setToken(result.token);
    return result.user;
  }

  async logout(): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/auth/logout`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
    });

    if (response.ok) {
      this.clearToken();
    }
  }

  async getCurrentUser(): Promise<User | null> {
    const token = this.getToken();
    if (!token) return null;

    try {
      const response = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: this.getAuthHeaders(),
      });

      if (!response.ok) {
        this.clearToken();
        return null;
      }

      return await response.json();
    } catch (error) {
      this.clearToken();
      return null;
    }
  }

  // Leaderboard
  async getLeaderboard(limit: number = 10, gameMode?: 'pass-through' | 'walls'): Promise<LeaderboardEntry[]> {
    const params = new URLSearchParams({
      limit: limit.toString(),
    });
    if (gameMode) {
      params.append('gameMode', gameMode);
    }

    const response = await fetch(`${API_BASE_URL}/leaderboard?${params}`);
    if (!response.ok) {
      throw new Error('Failed to fetch leaderboard');
    }

    const data = await response.json();
    return data.entries;
  }

  async submitScore(score: number, gameMode: 'pass-through' | 'walls'): Promise<LeaderboardEntry> {
    const response = await fetch(`${API_BASE_URL}/leaderboard`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ score, game_mode: gameMode }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail?.error?.message || 'Failed to submit score');
    }

    return await response.json();
  }

  // Watch endpoints
  async getActivePlayers(): Promise<ActivePlayer[]> {
    const response = await fetch(`${API_BASE_URL}/watch/active`);
    if (!response.ok) {
      throw new Error('Failed to fetch active players');
    }

    const data = await response.json();
    return data.players;
  }

  async startGameSession(gameMode: 'pass-through' | 'walls'): Promise<{ sessionId: string }> {
    const response = await fetch(`${API_BASE_URL}/watch/start`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ gameMode }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail?.error?.message || 'Failed to start game session');
    }

    const data = await response.json();
    return { sessionId: data.sessionId };
  }

  async updateGameState(sessionId: string, gameState: GameState): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/watch/update/${sessionId}`, {
      method: 'PUT',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ gameState }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail?.error?.message || 'Failed to update game state');
    }
  }

  async endGameSession(
    sessionId: string,
    finalScore: number,
    gameMode: 'pass-through' | 'walls'
  ): Promise<LeaderboardEntry> {
    const response = await fetch(`${API_BASE_URL}/watch/end/${sessionId}`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ finalScore, gameMode }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail?.error?.message || 'Failed to end game session');
    }

    const data = await response.json();
    return data.leaderboardEntry;
  }
}
```

## Key Differences from Mocks

### 1. Error Format
The backend returns errors in this format:
```json
{
  "detail": {
    "error": {
      "code": "ERROR_CODE",
      "message": "Human-readable error message"
    }
  }
}
```

Update your error handling to check `error.detail?.error?.message`.

### 2. Response Formats
- **Signup/Login**: Returns `{ user, token }` (same as mocks)
- **Leaderboard GET**: Returns `{ entries, total, limit, offset }` (not just array)
- **Watch Active**: Returns `{ players: [...] }` (not just array)

### 3. Authentication Required
These endpoints require authentication (include `Authorization: Bearer <token>`):
- `POST /leaderboard` (submit score)
- `POST /watch/start`
- `PUT /watch/update/:sessionId`
- `POST /watch/end/:sessionId`
- `POST /auth/logout`
- `GET /auth/me`

### 4. Field Name Differences
- Backend uses `game_mode` in request bodies, but accepts `gameMode` in query params
- Response fields match your TypeScript interfaces

## WebSocket Support

The backend also supports WebSocket connections for real-time updates:

```typescript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  switch (message.type) {
    case 'connected':
      console.log('Connected:', message.connectionId);
      break;
    case 'player:update':
      // Update player game state
      break;
    case 'player:join':
      // New player joined
      break;
    case 'player:leave':
      // Player left
      break;
  }
};

// Subscribe to a player
ws.send(JSON.stringify({
  type: 'subscribe',
  playerId: 'session-id'
}));
```

## Testing the Integration

1. **Start the backend server**:
   ```bash
   cd snake-game-be
   source venv/bin/activate
   uvicorn app.main:app --reload
   ```

2. **Update your frontend `.env`**:
   ```
   REACT_APP_API_URL=http://localhost:8000/api/v1
   ```

3. **Test the endpoints** using Swagger UI at http://localhost:8000/docs

## Error Handling

### Common Error Codes
- `EMAIL_EXISTS` - Email already registered
- `USERNAME_EXISTS` - Username already taken
- `INVALID_CREDENTIALS` - Wrong username/password
- `INVALID_TOKEN` - Expired or invalid JWT
- `SESSION_NOT_FOUND` - Game session doesn't exist
- `FORBIDDEN` - Session doesn't belong to user

### HTTP Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized (missing/invalid token)
- `403` - Forbidden (not authorized for resource)
- `404` - Not Found
- `409` - Conflict (duplicate email/username)
- `422` - Validation Error

## Validation Rules

### Username
- 3-20 characters
- Alphanumeric and underscore only
- Pattern: `^[a-zA-Z0-9_]+$`

### Password
- Minimum 8 characters

### Email
- Valid email format

### Score
- Must be >= 0

### Game Mode
- Must be `'pass-through'` or `'walls'`

## CORS Configuration

The backend is configured to accept requests from:
- `http://localhost:5173` (Vite default)
- `http://localhost:3000` (React default)

If you're using a different port, update `app/main.py` in the backend.

## Next Steps

1. Update `src/services/api.ts` with the code above
2. Update error handling to match the new error format
3. Test authentication flow (signup → login → get me)
4. Test leaderboard submission
5. Test watch endpoints if using that feature
6. Update environment variables for production

## Support

- **API Docs**: http://localhost:8000/docs
- **Backend Repo**: https://github.com/dog-face/snake-game-be
- **OpenAPI Spec**: http://localhost:8000/openapi.json

## Notes

- Tokens expire after 24 hours (configurable)
- Active sessions timeout after 5 minutes of inactivity
- All timestamps are in ISO 8601 format
- The backend uses async SQLAlchemy for better performance

