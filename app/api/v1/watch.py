from typing import Any, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete
from app.api import deps
from app.core.config import settings
from app.models.active_session import ActiveSession
from app.models.user import User
from app.models.leaderboard import Leaderboard
from app.schemas.watch import (
    ActivePlayersResponse,
    ActivePlayer,
    WatchStartRequest,
    WatchStartResponse,
    WatchUpdateRequest,
    WatchUpdateResponse,
    WatchEndRequest,
    WatchEndResponse,
    GameState,
)
from app.api.v1.websocket import (
    broadcast_player_update,
    broadcast_player_join,
    broadcast_player_leave,
)

router = APIRouter()

@router.get("/active", response_model=ActivePlayersResponse)
async def get_active_players(
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Get list of currently active players (players with active game sessions).
    """
    # Calculate cutoff time (sessions updated within SESSION_TIMEOUT)
    cutoff_time = datetime.utcnow() - timedelta(seconds=settings.SESSION_TIMEOUT)
    
    # Query active sessions
    result = await db.execute(
        select(ActiveSession).filter(
            ActiveSession.last_updated_at >= cutoff_time
        ).order_by(ActiveSession.last_updated_at.desc())
    )
    sessions = result.scalars().all()
    
    # Convert to ActivePlayer schema
    players = []
    for session in sessions:
        # Parse game_state JSON to GameState
        game_state_dict = session.game_state if isinstance(session.game_state, dict) else session.game_state
        game_state = GameState(**game_state_dict)
        
        players.append(ActivePlayer(
            id=session.id,
            userId=session.user_id,
            username=session.username,
            score=session.score,
            gameMode=session.game_mode,
            gameState=game_state,
            startedAt=session.started_at,
            lastUpdatedAt=session.last_updated_at,
        ))
    
    return {"players": players}

@router.get("/active/{playerId}", response_model=ActivePlayer)
async def get_active_player(
    playerId: str = Path(...),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Get specific active player's game state.
    """
    # Calculate cutoff time
    cutoff_time = datetime.utcnow() - timedelta(seconds=settings.SESSION_TIMEOUT)
    
    # Query session
    result = await db.execute(
        select(ActiveSession).filter(
            and_(
                ActiveSession.id == playerId,
                ActiveSession.last_updated_at >= cutoff_time
            )
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "SESSION_NOT_FOUND",
                    "message": "Player session not found or not active"
                }
            }
        )
    
    # Parse game_state
    game_state_dict = session.game_state if isinstance(session.game_state, dict) else session.game_state
    game_state = GameState(**game_state_dict)
    
    return ActivePlayer(
        id=session.id,
        userId=session.user_id,
        username=session.username,
        score=session.score,
        gameMode=session.game_mode,
        gameState=game_state,
        startedAt=session.started_at,
        lastUpdatedAt=session.last_updated_at,
    )

@router.post("/start", response_model=WatchStartResponse, status_code=status.HTTP_201_CREATED)
async def start_game_session(
    *,
    db: AsyncSession = Depends(deps.get_db),
    request: WatchStartRequest,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Start a new game session (for tracking active players).
    """
    # Create initial game state
    initial_game_state = {
        "snake": [{"x": 10, "y": 10}, {"x": 9, "y": 10}, {"x": 8, "y": 10}],
        "food": {"x": 15, "y": 15},
        "direction": "right",
        "score": 0,
        "gameOver": False,
    }
    
    session = ActiveSession(
        user_id=current_user.id,
        username=current_user.username,
        game_mode=request.gameMode.value,
        game_state=initial_game_state,
        score=0,
    )
    
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    # Broadcast player join event
    player_data = {
        "id": session.id,
        "username": session.username,
        "score": session.score,
        "gameMode": session.game_mode,
    }
    await broadcast_player_join(session.id, player_data)
    
    return WatchStartResponse(
        sessionId=session.id,
        gameMode=request.gameMode,
        startedAt=session.started_at,
    )

@router.put("/update/{sessionId}", response_model=WatchUpdateResponse)
async def update_game_session(
    sessionId: str = Path(...),
    *,
    db: AsyncSession = Depends(deps.get_db),
    request: WatchUpdateRequest,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Update game state for an active session.
    """
    # Query session
    result = await db.execute(
        select(ActiveSession).filter(ActiveSession.id == sessionId)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "SESSION_NOT_FOUND",
                    "message": "Session not found"
                }
            }
        )
    
    # Check ownership
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "FORBIDDEN",
                    "message": "Session doesn't belong to authenticated user"
                }
            }
        )
    
    # Update session
    session.game_state = request.gameState.model_dump()
    session.score = request.gameState.score
    session.last_updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(session)
    
    # Broadcast player update event
    player_data = {
        "id": session.id,
        "username": session.username,
        "score": session.score,
        "gameMode": session.game_mode,
        "gameState": request.gameState.model_dump(),
    }
    await broadcast_player_update(session.id, player_data)
    
    return WatchUpdateResponse(
        message="Game state updated",
        lastUpdatedAt=session.last_updated_at,
    )

@router.post("/end/{sessionId}", response_model=WatchEndResponse)
async def end_game_session(
    sessionId: str = Path(...),
    *,
    db: AsyncSession = Depends(deps.get_db),
    request: WatchEndRequest,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    End a game session (called when game ends).
    """
    # Query session
    result = await db.execute(
        select(ActiveSession).filter(ActiveSession.id == sessionId)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "SESSION_NOT_FOUND",
                    "message": "Session not found"
                }
            }
        )
    
    # Check ownership
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "FORBIDDEN",
                    "message": "Session doesn't belong to authenticated user"
                }
            }
        )
    
    # Create leaderboard entry
    from datetime import date
    leaderboard_entry = Leaderboard(
        user_id=current_user.id,
        username=current_user.username,
        score=request.finalScore,
        game_mode=request.gameMode.value,
        date=date.today(),
    )
    db.add(leaderboard_entry)
    
    # Broadcast player leave event before deleting
    await broadcast_player_leave(sessionId)
    
    # Delete session using async SQLAlchemy delete statement
    await db.execute(delete(ActiveSession).filter(ActiveSession.id == sessionId))
    await db.commit()
    
    return WatchEndResponse(
        message="Session ended",
        leaderboardEntry={
            "id": leaderboard_entry.id,
            "username": leaderboard_entry.username,
            "score": leaderboard_entry.score,
            "gameMode": leaderboard_entry.game_mode,
            "date": leaderboard_entry.date.isoformat(),
        }
    )

