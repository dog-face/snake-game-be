# Snake Game Backend API

FastAPI backend for the Snake Game application with authentication, leaderboard, and real-time game state tracking.

## Quick Start

### 1. Activate Virtual Environment
```bash
source venv/bin/activate
```

### 2. Start the Server
```bash
uvicorn app.main:app --reload
```

The server will start at `http://localhost:8000`

### 3. Access API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Development

### Running with Auto-reload
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Running Tests
```bash
# Activate venv first
source venv/bin/activate

# Run all tests
pytest

# Or use the helper script
./run_tests.sh
```

### Database Migrations
```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

## Environment Variables

Create a `.env` file in the project root:

```env
DATABASE_URL=sqlite:///./snake_game.db
SECRET_KEY=your-secret-key-here-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=1440
SESSION_TIMEOUT=300
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/signup` - Create new user
- `POST /api/v1/auth/login` - Login user
- `POST /api/v1/auth/logout` - Logout user
- `GET /api/v1/auth/me` - Get current user

### Leaderboard
- `GET /api/v1/leaderboard` - Get leaderboard entries
- `POST /api/v1/leaderboard` - Submit score

### Watch (Active Players)
- `GET /api/v1/watch/active` - Get active players
- `GET /api/v1/watch/active/{playerId}` - Get specific player
- `POST /api/v1/watch/start` - Start game session
- `PUT /api/v1/watch/update/{sessionId}` - Update game state
- `POST /api/v1/watch/end/{sessionId}` - End game session

### WebSocket
- `WS /ws` - Real-time game state updates

## Project Structure

```
snake-game-be/
├── app/
│   ├── api/v1/          # API route handlers
│   ├── core/            # Configuration and security
│   ├── db/              # Database session and models
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   └── main.py          # FastAPI application
├── tests/               # Test suite
├── alembic/             # Database migrations
└── requirements.txt     # Python dependencies
```

## Technology Stack

- **FastAPI** - Web framework
- **SQLAlchemy (Async)** - ORM
- **Alembic** - Database migrations
- **Pydantic** - Data validation
- **JWT** - Authentication
- **WebSocket** - Real-time updates

## License

MIT

