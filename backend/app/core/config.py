from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = "sqlite:///./mailmind.db"
    
    # Gmail API
    gmail_client_id: Optional[str] = None
    gmail_client_secret: Optional[str] = None
    gmail_redirect_uri: str = "http://localhost:8000/auth/gmail/callback"
    
    # OpenAI API
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4"
    
    # MCP Configuration
    mcp_server_url: Optional[str] = None
    mcp_api_key: Optional[str] = None
    
    # Security
    secret_key: str = "your_secret_key_here_change_in_production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Development
    debug: bool = True
    log_level: str = "INFO"
    
    # Export
    export_dir: str = "./exports"
    max_export_size: str = "100MB"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
