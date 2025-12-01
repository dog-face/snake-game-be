from typing import List
try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal
from pydantic import BaseModel, field_validator
from datetime import datetime
from app.schemas.leaderboard import GameMode

class Position(BaseModel):
    x: int
    y: int
    
    @field_validator('x', 'y')
    @classmethod
    def validate_coordinate(cls, v: int) -> int:
        if not (0 <= v <= 19):
            raise ValueError('Position coordinates must be between 0 and 19 (20x20 grid)')
        return v

class GameState(BaseModel):
    snake: List[Position]
    food: Position
    direction: Literal['up', 'down', 'left', 'right']
    score: int
    gameOver: bool
    
    @field_validator('score')
    @classmethod
    def validate_score(cls, v: int) -> int:
        if v < 0:
            raise ValueError('Score must be non-negative')
        return v

class ActivePlayer(BaseModel):
    id: str
    userId: str
    username: str
    score: int
    gameMode: GameMode
    gameState: GameState
    startedAt: datetime
    lastUpdatedAt: datetime
    
    class Config:
        from_attributes = True

class WatchStartRequest(BaseModel):
    gameMode: GameMode

class WatchStartResponse(BaseModel):
    sessionId: str
    gameMode: GameMode
    startedAt: datetime

class WatchUpdateRequest(BaseModel):
    gameState: GameState

class WatchUpdateResponse(BaseModel):
    message: str
    lastUpdatedAt: datetime

class WatchEndRequest(BaseModel):
    finalScore: int
    gameMode: GameMode
    
    @field_validator('finalScore')
    @classmethod
    def validate_score(cls, v: int) -> int:
        if v < 0:
            raise ValueError('Score must be non-negative')
        return v

class WatchEndResponse(BaseModel):
    message: str
    leaderboardEntry: dict

class ActivePlayersResponse(BaseModel):
    players: List[ActivePlayer]

