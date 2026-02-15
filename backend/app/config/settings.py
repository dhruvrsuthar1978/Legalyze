# app/config/settings.py

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Legalyze API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_PREFIX: str = "/api"
    
    # Frontend
    FRONTEND_URL: str = "http://localhost:5173"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = ""

    # Database
    MONGODB_URI: str
    DB_NAME: str = "legalyze_db"

    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # AWS (Optional)
    AWS_ACCESS_KEY: str = ""
    AWS_SECRET_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    S3_BUCKET: str = ""
    
    # Email (Optional)
    SMTP_SERVER: str = ""
    SMTP_PORT: int | None = None
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = ""
    FROM_NAME: str = "Legalyze"
    
    # AI Models (Optional)
    OPENAI_API_KEY: str = ""
    HUGGINGFACE_API_KEY: str = ""
    
    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 25
    ALLOWED_FILE_TYPES: str = "application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Security
    BCRYPT_ROUNDS: int = 12
    PASSWORD_MIN_LENGTH: int = 8

    # Firebase (Optional)
    FIREBASE_CREDENTIALS_PATH: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


settings = Settings()