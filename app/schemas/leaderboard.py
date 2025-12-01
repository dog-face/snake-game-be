from typing import Optional, List
from pydantic import BaseModel, field_validator
from datetime import date, datetime
from enum import Enum

class GameMode(str, Enum):
    PASS_THROUGH = "pass-through"
    WALLS = "walls"

class LeaderboardBase(BaseModel):
    score: int
    game_mode: GameMode
    
    @field_validator('score')
    @classmethod
    def validate_score(cls, v: int) -> int:
        if v < 0:
            raise ValueError('Score must be non-negative')
        return v

class LeaderboardCreate(LeaderboardBase):
    pass

class LeaderboardEntry(LeaderboardBase):
    id: str
    username: str
    date: date
    
    class Config:
        from_attributes = True

class LeaderboardResponse(BaseModel):
    entries: List[LeaderboardEntry]
    total: int
    limit: int
    offset: int
