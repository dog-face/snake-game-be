from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.user import User
from app.schemas.user import UserCreate, User as UserSchema, LoginSchema

router = APIRouter()

@router.post("/signup", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_user(
    *,
    db: AsyncSession = Depends(deps.get_db),
    user_in: UserCreate,
) -> Any:
    """
    Create new user.
    """
    # Check if email exists
    result = await db.execute(select(User).filter(User.email == user_in.email))
    user = result.scalar_one_or_none()
    if user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": "EMAIL_EXISTS",
                    "message": "The user with this email already exists in the system."
                }
            }
        )
    
    # Check if username exists
    result = await db.execute(select(User).filter(User.username == user_in.username))
    user = result.scalar_one_or_none()
    if user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": "USERNAME_EXISTS",
                    "message": "The user with this username already exists in the system."
                }
            }
        )
    
    user = User(
        email=user_in.email,
        username=user_in.username,
        password_hash=security.get_password_hash(user_in.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        user.id, expires_delta=access_token_expires
    )
    
    return {
        "user": UserSchema.model_validate(user),
        "token": access_token
    }

@router.post("/login", response_model=dict)
async def login(
    *,
    db: AsyncSession = Depends(deps.get_db),
    login_data: LoginSchema,
) -> Any:
    """
    Authenticate user and return JWT token.
    """
    result = await db.execute(select(User).filter(User.username == login_data.username))
    user = result.scalar_one_or_none()
    
    if not user or not security.verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "INVALID_CREDENTIALS",
                    "message": "Invalid username or password"
                }
            }
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        user.id, expires_delta=access_token_expires
    )
    
    return {
        "user": UserSchema.model_validate(user),
        "token": access_token
    }

@router.post("/logout")
async def logout(
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Logout user (optional - mainly for token blacklisting if implemented).
    """
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=UserSchema)
async def read_users_me(
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get current user.
    """
    return current_user
