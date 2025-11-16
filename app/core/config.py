from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application configuration loaded from environment variables"""

    # Zoho Cliq Configuration
    zoho_cliq_webhook_url: str = Field(
        ..., description="Webhook URL for sending messages to Zoho Cliq"
    )
    zoho_cliq_token: str = Field(
        ..., description="Authentication token for Zoho Cliq API"
    )

    # GitHub Configuration
    github_webhook_secret: str = Field(
        default="", description="Secret for verifying GitHub webhook signatures"
    )

    # Sentry Configuration
    sentry_dsn: str = Field(
        default="", description="Sentry DSN for error tracking"
    )

     # Encryption Configuration
    encryption_key: str = Field(
        default="", description="Fernet encryption key for credentials"
    )

    # Database Configuration
    database_url: str = Field(
        default="postgresql://vigil_user:password@localhost:5432/vigil",
        description="Database URL for SQLAlchemy"
    )

    # Server Configuration
    server_host: str = Field(
        default="0.0.0.0", description="Server host address"
    )
    server_port: int = Field(
        default=8000, description="Server port number"
    )
    debug: bool = Field(
        default=False, description="Enable debug mode"
    )
    environment: str = Field(
        default="development", description="Environment: development, staging, production"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Create a singleton instance
settings = Settings()