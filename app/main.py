from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.active_session import ActiveSession
from sqlalchemy import select
from datetime import datetime, timedelta

async def cleanup_stale_sessions():
    """Background task to clean up stale sessions"""
    while True:
        try:
            async with AsyncSessionLocal() as db:
                cutoff_time = datetime.utcnow() - timedelta(seconds=settings.SESSION_TIMEOUT)
                result = await db.execute(
                    select(ActiveSession).filter(
                        ActiveSession.last_updated_at < cutoff_time
                    )
                )
                stale_sessions = result.scalars().all()
                
                for session in stale_sessions:
                    await db.delete(session)
                
                await db.commit()
                
                if stale_sessions:
                    print(f"Cleaned up {len(stale_sessions)} stale session(s)")
        except Exception as e:
            print(f"Error cleaning up sessions: {e}")
        
        # Run cleanup every minute
        await asyncio.sleep(60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    cleanup_task = asyncio.create_task(cleanup_stale_sessions())
    yield
    # Shutdown
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass

app = FastAPI(
    title="Snake Game API",
    description="""
    RESTful API for the Snake Game application. Provides endpoints for user authentication, 
    leaderboard management, and real-time game state tracking for the watch feature.
    
    ## Authentication
    Most endpoints require JWT authentication. Include the token in the Authorization header:
    ```
    Authorization: Bearer <your-jwt-token>
    ```
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    openapi_version="3.0.3",
    contact={
        "name": "API Support",
        "email": "support@snakegame.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    servers=[
        {"url": "http://localhost:8000/api/v1", "description": "Local development server"},
        {"url": "https://api.snakegame.com/api/v1", "description": "Production server"},
    ],
)

origins = [
    "http://localhost:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.v1 import auth, leaderboard, watch, websocket

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(leaderboard.router, prefix="/api/v1/leaderboard", tags=["leaderboard"])
app.include_router(watch.router, prefix="/api/v1/watch", tags=["watch"])
app.include_router(websocket.router, tags=["websocket"])

@app.get("/")
async def root():
    return {"message": "Welcome to Snake Game API"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
