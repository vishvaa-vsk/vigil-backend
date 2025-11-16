from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base


class User(Base):
    """User model - stores Zoho Cliq user information"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    zoho_user_id = Column(String(255), unique=True, index=True, nullable=False)
    zoho_username = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    github_integrations = relationship("GitHubIntegration", back_populates="user", cascade="all, delete-orphan")
    sentry_integrations = relationship("SentryIntegration", back_populates="user", cascade="all, delete-orphan")
    docker_integrations = relationship("DockerIntegration", back_populates="user", cascade="all, delete-orphan")
    firebase_integrations = relationship("FirebaseIntegration", back_populates="user", cascade="all, delete-orphan")
    alert_preferences = relationship("AlertPreference", back_populates="user", cascade="all, delete-orphan")


class GitHubIntegration(Base):
    """GitHub integration configuration per user"""
    __tablename__ = "github_integrations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    github_token_encrypted = Column(Text, nullable=False)
    repository = Column(String(255), nullable=False)
    webhook_secret = Column(String(255), nullable=False)
    enabled = Column(Boolean, default=True)
    alert_level = Column(String(50), default="all")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="github_integrations")

    # Properties for encrypted/decrypted access
    @property
    def github_token(self) -> str:
        """Get decrypted GitHub token"""
        from app.core.encryption import credential_encryption
        return credential_encryption.decrypt(self.github_token_encrypted)
    
    @github_token.setter
    def github_token(self, value: str):
        """Set and encrypt GitHub token"""
        from app.core.encryption import credential_encryption
        self.github_token_encrypted = credential_encryption.encrypt(value)


class SentryIntegration(Base):
    """Sentry integration configuration per user"""
    __tablename__ = "sentry_integrations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    sentry_dsn_encrypted = Column(Text, nullable=False)
    sentry_org_slug = Column(String(255), nullable=False)
    sentry_project_slug = Column(String(255), nullable=False)
    enabled = Column(Boolean, default=True)
    alert_level = Column(String(50), default="error")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="sentry_integrations")

    # Properties for encrypted/decrypted access
    @property
    def sentry_dsn(self) -> str:
        """Get decrypted Sentry DSN"""
        from app.core.encryption import credential_encryption
        return credential_encryption.decrypt(self.sentry_dsn_encrypted)
    
    @sentry_dsn.setter
    def sentry_dsn(self, value: str):
        """Set and encrypt Sentry DSN"""
        from app.core.encryption import credential_encryption
        self.sentry_dsn_encrypted = credential_encryption.encrypt(value)


class DockerIntegration(Base):
    """Docker integration configuration per user"""
    __tablename__ = "docker_integrations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    docker_registry_url = Column(String(255), nullable=False)
    registry_username = Column(String(255), nullable=False)
    registry_password_encrypted = Column(Text, nullable=False)
    enabled = Column(Boolean, default=True)
    alert_on = Column(String(50), default="all")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="docker_integrations")

    # Properties for encrypted/decrypted access
    @property
    def registry_password(self) -> str:
        """Get decrypted Docker registry password"""
        from app.core.encryption import credential_encryption
        return credential_encryption.decrypt(self.registry_password_encrypted)
    
    @registry_password.setter
    def registry_password(self, value: str):
        """Set and encrypt Docker registry password"""
        from app.core.encryption import credential_encryption
        self.registry_password_encrypted = credential_encryption.encrypt(value)


class FirebaseIntegration(Base):
    """Firebase Crashlytics integration configuration per user"""
    __tablename__ = "firebase_integrations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    firebase_project_id = Column(String(255), nullable=False)
    firebase_api_key_encrypted = Column(Text, nullable=False)
    enabled = Column(Boolean, default=True)
    alert_level = Column(String(50), default="error")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="firebase_integrations")

    # Properties for encrypted/decrypted access
    @property
    def firebase_api_key(self) -> str:
        """Get decrypted Firebase API key"""
        from app.core.encryption import credential_encryption
        return credential_encryption.decrypt(self.firebase_api_key_encrypted)
    
    @firebase_api_key.setter
    def firebase_api_key(self, value: str):
        """Set and encrypt Firebase API key"""
        from app.core.encryption import credential_encryption
        self.firebase_api_key_encrypted = credential_encryption.encrypt(value)


class AlertPreference(Base):
    """User alert preferences and notification settings"""
    __tablename__ = "alert_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    channel_id = Column(String(255), nullable=False)
    quiet_hours_start = Column(String(5), nullable=True)
    quiet_hours_end = Column(String(5), nullable=True)
    timezone = Column(String(50), default="UTC")
    mute_notifications = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="alert_preferences")


class AlertLog(Base):
    """Log of all alerts sent - for audit trail and analytics"""
    __tablename__ = "alert_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    alert_type = Column(String(50), nullable=False)
    event_type = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    severity = Column(String(50), nullable=False)
    message = Column(Text, nullable=True)
    source_id = Column(String(255), nullable=True)
    zoho_message_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)