from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Snake Game API"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "your-secret-key-here"  # TODO: Change in production
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Database
    DATABASE_URL: str = "sqlite:///./snake_game.db"
    
    # Session timeout in seconds (default 5 minutes)
    SESSION_TIMEOUT: int = 300
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
