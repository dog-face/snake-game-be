from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.api import deps
from app.models.leaderboard import Leaderboard
from app.models.user import User
from app.schemas.leaderboard import LeaderboardCreate, LeaderboardResponse, LeaderboardEntry, GameMode

router = APIRouter()

@router.get("", response_model=LeaderboardResponse)
async def get_leaderboard(
    db: AsyncSession = Depends(deps.get_db),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    gameMode: Optional[str] = Query(None, alias="gameMode"),
) -> Any:
    """
    Get leaderboard entries, sorted by score (descending).
    """
    # Support both gameMode and game_mode query params
    game_mode = gameMode
    
    # Build query
    query = select(Leaderboard)
    if game_mode:
        if game_mode not in ["pass-through", "walls"]:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "INVALID_GAME_MODE",
                        "message": "Game mode must be 'pass-through' or 'walls'"
                    }
                }
            )
        query = query.filter(Leaderboard.game_mode == game_mode)
    
    # Get total count
    count_query = select(func.count()).select_from(Leaderboard)
    if game_mode:
        count_query = count_query.filter(Leaderboard.game_mode == game_mode)
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()
    
    # Get entries
    entries_result = await db.execute(
        query.order_by(desc(Leaderboard.score)).offset(offset).limit(limit)
    )
    entries = entries_result.scalars().all()
    
    return {
        "entries": entries,
        "total": total,
        "limit": limit,
        "offset": offset,
    }

@router.post("", response_model=LeaderboardEntry, status_code=201)
async def submit_score(
    *,
    db: AsyncSession = Depends(deps.get_db),
    score_in: LeaderboardCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Submit a new score entry.
    """
    entry = Leaderboard(
        user_id=current_user.id,
        username=current_user.username,
        score=score_in.score,
        game_mode=score_in.game_mode.value,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry
