import pytest
from pydantic import ValidationError
from app.schemas.user import UserCreate, LoginSchema
from app.schemas.leaderboard import LeaderboardCreate, GameMode
from app.schemas.watch import Position, GameState, WatchStartRequest

class TestUserSchemas:
    """Test user-related schemas"""
    
    def test_user_create_valid(self):
        """Test creating valid user"""
        user = UserCreate(
            username="testuser",
            email="test@example.com",
            password="password123"
        )
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.password == "password123"
    
    def test_user_create_invalid_username_short(self):
        """Test user creation with username too short"""
        with pytest.raises(ValidationError):
            UserCreate(
                username="ab",
                email="test@example.com",
                password="password123"
            )
    
    def test_user_create_invalid_username_long(self):
        """Test user creation with username too long"""
        with pytest.raises(ValidationError):
            UserCreate(
                username="a" * 21,
                email="test@example.com",
                password="password123"
            )
    
    def test_user_create_invalid_username_characters(self):
        """Test user creation with invalid username characters"""
        with pytest.raises(ValidationError):
            UserCreate(
                username="user-name!",
                email="test@example.com",
                password="password123"
            )
    
    def test_user_create_invalid_password_short(self):
        """Test user creation with password too short"""
        with pytest.raises(ValidationError):
            UserCreate(
                username="testuser",
                email="test@example.com",
                password="short"
            )
    
    def test_login_schema_valid(self):
        """Test valid login schema"""
        login = LoginSchema(username="testuser", password="password123")
        assert login.username == "testuser"
        assert login.password == "password123"

class TestLeaderboardSchemas:
    """Test leaderboard-related schemas"""
    
    def test_leaderboard_create_valid(self):
        """Test creating valid leaderboard entry"""
        entry = LeaderboardCreate(score=100, game_mode=GameMode.PASS_THROUGH)
        assert entry.score == 100
        assert entry.game_mode == GameMode.PASS_THROUGH
    
    def test_leaderboard_create_negative_score(self):
        """Test creating leaderboard entry with negative score"""
        with pytest.raises(ValidationError):
            LeaderboardCreate(score=-10, game_mode=GameMode.PASS_THROUGH)
    
    def test_leaderboard_create_walls_mode(self):
        """Test creating leaderboard entry with walls mode"""
        entry = LeaderboardCreate(score=200, game_mode=GameMode.WALLS)
        assert entry.game_mode == GameMode.WALLS

class TestWatchSchemas:
    """Test watch-related schemas"""
    
    def test_position_valid(self):
        """Test creating valid position"""
        pos = Position(x=10, y=15)
        assert pos.x == 10
        assert pos.y == 15
    
    def test_position_invalid_x_low(self):
        """Test position with x too low"""
        with pytest.raises(ValidationError):
            Position(x=-1, y=10)
    
    def test_position_invalid_x_high(self):
        """Test position with x too high"""
        with pytest.raises(ValidationError):
            Position(x=20, y=10)
    
    def test_position_invalid_y_low(self):
        """Test position with y too low"""
        with pytest.raises(ValidationError):
            Position(x=10, y=-1)
    
    def test_position_invalid_y_high(self):
        """Test position with y too high"""
        with pytest.raises(ValidationError):
            Position(x=10, y=20)
    
    def test_game_state_valid(self):
        """Test creating valid game state"""
        game_state = GameState(
            snake=[Position(x=10, y=10), Position(x=9, y=10)],
            food=Position(x=15, y=15),
            direction="right",
            score=10,
            gameOver=False,
        )
        assert len(game_state.snake) == 2
        assert game_state.score == 10
        assert game_state.gameOver is False
    
    def test_game_state_negative_score(self):
        """Test game state with negative score"""
        with pytest.raises(ValidationError):
            GameState(
                snake=[Position(x=10, y=10)],
                food=Position(x=15, y=15),
                direction="right",
                score=-10,
                gameOver=False,
            )
    
    def test_watch_start_request_valid(self):
        """Test valid watch start request"""
        request = WatchStartRequest(gameMode=GameMode.PASS_THROUGH)
        assert request.gameMode == GameMode.PASS_THROUGH

