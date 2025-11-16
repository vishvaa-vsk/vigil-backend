from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from app.db.database import get_db
from app.db.models import(
    User,
    GitHubIntegration,
    SentryIntegration,
    DockerIntegration,
    FirebaseIntegration,
    AlertPreference,
)

router = APIRouter()

# ============================================================================
# Request/Response Models
# ============================================================================

class GitHubConfigRequest(BaseModel):
    """GitHub integration configuration request"""
    zoho_user_id: str = Field(..., description="Zoho user ID")
    github_token: str = Field(..., description="GitHub personal access token")
    repository: str = Field(..., description="GitHub repository (owner/repo)")
    webhook_secret: str = Field(..., description="Webhook secret for verification")
    alert_level: str = Field(default="all", description="Alert level: all, major, critical")


class SentryConfigRequest(BaseModel):
    """Sentry integration configuration request"""
    zoho_user_id: str = Field(..., description="Zoho user ID")
    sentry_dsn: str = Field(..., description="Sentry DSN")
    sentry_org_slug: str = Field(..., description="Sentry organization slug")
    sentry_project_slug: str = Field(..., description="Sentry project slug")
    alert_level: str = Field(default="error", description="Alert level: debug, warning, error, fatal")


class DockerConfigRequest(BaseModel):
    """Docker integration configuration request"""
    zoho_user_id: str = Field(..., description="Zoho user ID")
    docker_registry_url: str = Field(..., description="Docker registry URL")
    registry_username: str = Field(..., description="Docker registry username")
    registry_password: str = Field(..., description="Docker registry password")
    alert_on: str = Field(default="all", description="Alert on: all, failures, push")


class FirebaseConfigRequest(BaseModel):
    """Firebase integration configuration request"""
    zoho_user_id: str = Field(..., description="Zoho user ID")
    firebase_project_id: str = Field(..., description="Firebase project ID")
    firebase_api_key: str = Field(..., description="Firebase API key")
    alert_level: str = Field(default="error", description="Alert level: warning, error, fatal")


class AlertPreferenceRequest(BaseModel):
    """Alert preference configuration request"""
    zoho_user_id: str = Field(..., description="Zoho user ID")
    channel_id: str = Field(..., description="Zoho Cliq channel ID")
    quiet_hours_start: str = Field(default=None, description="Quiet hours start (HH:MM)")
    quiet_hours_end: str = Field(default=None, description="Quiet hours end (HH:MM)")
    timezone: str = Field(default="UTC", description="User timezone")
    mute_notifications: bool = Field(default=False, description="Mute all notifications")


class ConfigurationResponse(BaseModel):
    """Generic configuration response"""
    status: str
    integration: str
    message: str


class IntegrationStatusResponse(BaseModel):
    """Integration status response"""
    github: dict
    sentry: dict
    docker: dict
    firebase: dict
    preferences: dict


# ============================================================================
# Helper Functions
# ============================================================================

def get_or_create_user(db: Session, zoho_user_id: str) -> User:
    """Get existing user or create new one"""
    user = db.query(User).filter(User.zoho_user_id == zoho_user_id).first()
    
    if not user:
        # Create new user with default values
        user = User(
            zoho_user_id=zoho_user_id,
            zoho_username=zoho_user_id.split("_")[0],  # Extract from ID
            email=f"{zoho_user_id}@zoho.com",  # Default email
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"✅ New user created: {zoho_user_id}")
    
    return user


# ============================================================================
# GitHub Configuration Endpoints
# ============================================================================

@router.post("/github", response_model=ConfigurationResponse, tags=["Configuration"])
async def configure_github(
    config: GitHubConfigRequest,
    db: Session = Depends(get_db),
):
    """
    Configure GitHub integration with encrypted token storage
    
    Args:
        config: GitHub configuration details
        db: Database session
    
    Returns:
        Configuration status response
    """
    try:
        # Get or create user
        user = get_or_create_user(db, config.zoho_user_id)
        
        # Check if GitHub integration exists
        existing = db.query(GitHubIntegration).filter(
            GitHubIntegration.user_id == user.id
        ).first()
        
        if existing:
            # Update existing
            existing.github_token = config.github_token  # Auto-encrypted via property
            existing.repository = config.repository
            existing.webhook_secret = config.webhook_secret
            existing.alert_level = config.alert_level
            db.commit()
            message = "GitHub integration updated successfully"
            print(f"✅ GitHub updated for user {config.zoho_user_id}")
        else:
            # Create new
            new_config = GitHubIntegration(
                user_id=user.id,
                github_token=config.github_token,  # Auto-encrypted via property
                repository=config.repository,
                webhook_secret=config.webhook_secret,
                alert_level=config.alert_level,
                enabled=True
            )
            db.add(new_config)
            db.commit()
            message = "GitHub integration configured successfully"
            print(f"✅ GitHub configured for user {config.zoho_user_id}")
        
        print(f"   Repository: {config.repository}")
        print(f"   Alert Level: {config.alert_level}")
        
        return ConfigurationResponse(
            status="success",
            integration="GitHub",
            message=message
        )
    
    except Exception as e:
        print(f"❌ GitHub configuration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Configuration failed: {str(e)}"
        )


# ============================================================================
# Sentry Configuration Endpoints
# ============================================================================

@router.post("/sentry", response_model=ConfigurationResponse, tags=["Configuration"])
async def configure_sentry(
    config: SentryConfigRequest,
    db: Session = Depends(get_db),
):
    """
    Configure Sentry integration with encrypted DSN storage
    
    Args:
        config: Sentry configuration details
        db: Database session
    
    Returns:
        Configuration status response
    """
    try:
        # Get or create user
        user = get_or_create_user(db, config.zoho_user_id)
        
        # Check if Sentry integration exists
        existing = db.query(SentryIntegration).filter(
            SentryIntegration.user_id == user.id
        ).first()
        
        if existing:
            # Update existing
            existing.sentry_dsn = config.sentry_dsn  # Auto-encrypted via property
            existing.sentry_org_slug = config.sentry_org_slug
            existing.sentry_project_slug = config.sentry_project_slug
            existing.alert_level = config.alert_level
            db.commit()
            message = "Sentry integration updated successfully"
            print(f"✅ Sentry updated for user {config.zoho_user_id}")
        else:
            # Create new
            new_config = SentryIntegration(
                user_id=user.id,
                sentry_dsn=config.sentry_dsn,  # Auto-encrypted via property
                sentry_org_slug=config.sentry_org_slug,
                sentry_project_slug=config.sentry_project_slug,
                alert_level=config.alert_level,
                enabled=True
            )
            db.add(new_config)
            db.commit()
            message = "Sentry integration configured successfully"
            print(f"✅ Sentry configured for user {config.zoho_user_id}")
        
        print(f"   Organization: {config.sentry_org_slug}")
        print(f"   Project: {config.sentry_project_slug}")
        print(f"   Alert Level: {config.alert_level}")
        
        return ConfigurationResponse(
            status="success",
            integration="Sentry",
            message=message
        )
    
    except Exception as e:
        print(f"❌ Sentry configuration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Configuration failed: {str(e)}"
        )


# ============================================================================
# Docker Configuration Endpoints
# ============================================================================

@router.post("/docker", response_model=ConfigurationResponse, tags=["Configuration"])
async def configure_docker(
    config: DockerConfigRequest,
    db: Session = Depends(get_db),
):
    """
    Configure Docker integration with encrypted password storage
    
    Args:
        config: Docker configuration details
        db: Database session
    
    Returns:
        Configuration status response
    """
    try:
        # Get or create user
        user = get_or_create_user(db, config.zoho_user_id)
        
        # Check if Docker integration exists
        existing = db.query(DockerIntegration).filter(
            DockerIntegration.user_id == user.id
        ).first()
        
        if existing:
            # Update existing
            existing.docker_registry_url = config.docker_registry_url
            existing.registry_username = config.registry_username
            existing.registry_password = config.registry_password  # Auto-encrypted via property
            existing.alert_on = config.alert_on
            db.commit()
            message = "Docker integration updated successfully"
            print(f"✅ Docker updated for user {config.zoho_user_id}")
        else:
            # Create new
            new_config = DockerIntegration(
                user_id=user.id,
                docker_registry_url=config.docker_registry_url,
                registry_username=config.registry_username,
                registry_password=config.registry_password,  # Auto-encrypted via property
                alert_on=config.alert_on,
                enabled=True
            )
            db.add(new_config)
            db.commit()
            message = "Docker integration configured successfully"
            print(f"✅ Docker configured for user {config.zoho_user_id}")
        
        print(f"   Registry: {config.docker_registry_url}")
        print(f"   Username: {config.registry_username}")
        print(f"   Alert On: {config.alert_on}")
        
        return ConfigurationResponse(
            status="success",
            integration="Docker",
            message=message
        )
    
    except Exception as e:
        print(f"❌ Docker configuration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Configuration failed: {str(e)}"
        )


# ============================================================================
# Firebase Configuration Endpoints
# ============================================================================

@router.post("/firebase", response_model=ConfigurationResponse, tags=["Configuration"])
async def configure_firebase(
    config: FirebaseConfigRequest,
    db: Session = Depends(get_db),
):
    """
    Configure Firebase integration with encrypted API key storage
    
    Args:
        config: Firebase configuration details
        db: Database session
    
    Returns:
        Configuration status response
    """
    try:
        # Get or create user
        user = get_or_create_user(db, config.zoho_user_id)
        
        # Check if Firebase integration exists
        existing = db.query(FirebaseIntegration).filter(
            FirebaseIntegration.user_id == user.id
        ).first()
        
        if existing:
            # Update existing
            existing.firebase_project_id = config.firebase_project_id
            existing.firebase_api_key = config.firebase_api_key  # Auto-encrypted via property
            existing.alert_level = config.alert_level
            db.commit()
            message = "Firebase integration updated successfully"
            print(f"✅ Firebase updated for user {config.zoho_user_id}")
        else:
            # Create new
            new_config = FirebaseIntegration(
                user_id=user.id,
                firebase_project_id=config.firebase_project_id,
                firebase_api_key=config.firebase_api_key,  # Auto-encrypted via property
                alert_level=config.alert_level,
                enabled=True
            )
            db.add(new_config)
            db.commit()
            message = "Firebase integration configured successfully"
            print(f"✅ Firebase configured for user {config.zoho_user_id}")
        
        print(f"   Project ID: {config.firebase_project_id}")
        print(f"   Alert Level: {config.alert_level}")
        
        return ConfigurationResponse(
            status="success",
            integration="Firebase",
            message=message
        )
    
    except Exception as e:
        print(f"❌ Firebase configuration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Configuration failed: {str(e)}"
        )


# ============================================================================
# Alert Preference Endpoints
# ============================================================================

@router.post("/preferences", response_model=ConfigurationResponse, tags=["Configuration"])
async def configure_alert_preferences(
    preferences: AlertPreferenceRequest,
    db: Session = Depends(get_db),
):
    """
    Configure alert preferences and notification settings
    
    Args:
        preferences: Alert preference details
        db: Database session
    
    Returns:
        Configuration status response
    """
    try:
        # Get or create user
        user = get_or_create_user(db, preferences.zoho_user_id)
        
        # Check if preference exists
        existing = db.query(AlertPreference).filter(
            AlertPreference.user_id == user.id
        ).first()
        
        if existing:
            # Update existing
            existing.channel_id = preferences.channel_id
            existing.quiet_hours_start = preferences.quiet_hours_start
            existing.quiet_hours_end = preferences.quiet_hours_end
            existing.timezone = preferences.timezone
            existing.mute_notifications = preferences.mute_notifications
            db.commit()
            message = "Alert preferences updated successfully"
            print(f"✅ Preferences updated for user {preferences.zoho_user_id}")
        else:
            # Create new
            new_preference = AlertPreference(
                user_id=user.id,
                channel_id=preferences.channel_id,
                quiet_hours_start=preferences.quiet_hours_start,
                quiet_hours_end=preferences.quiet_hours_end,
                timezone=preferences.timezone,
                mute_notifications=preferences.mute_notifications
            )
            db.add(new_preference)
            db.commit()
            message = "Alert preferences configured successfully"
            print(f"✅ Preferences configured for user {preferences.zoho_user_id}")
        
        print(f"   Channel: {preferences.channel_id}")
        print(f"   Timezone: {preferences.timezone}")
        
        return ConfigurationResponse(
            status="success",
            integration="AlertPreferences",
            message=message
        )
    
    except Exception as e:
        print(f"❌ Alert preference configuration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Configuration failed: {str(e)}"
        )


# ============================================================================
# Status Endpoints
# ============================================================================

@router.get("/status/{zoho_user_id}", response_model=IntegrationStatusResponse, tags=["Configuration"])
async def get_configuration_status(
    zoho_user_id: str,
    db: Session = Depends(get_db),
):
    """
    Get all configured integrations status for a user
    
    Args:
        zoho_user_id: Zoho user ID
        db: Database session
    
    Returns:
        Integration status for all services
    """
    try:
        # Get user
        user = db.query(User).filter(User.zoho_user_id == zoho_user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        github = db.query(GitHubIntegration).filter(
            GitHubIntegration.user_id == user.id
        ).first()
        
        sentry = db.query(SentryIntegration).filter(
            SentryIntegration.user_id == user.id
        ).first()
        
        docker = db.query(DockerIntegration).filter(
            DockerIntegration.user_id == user.id
        ).first()
        
        firebase = db.query(FirebaseIntegration).filter(
            FirebaseIntegration.user_id == user.id
        ).first()
        
        preferences = db.query(AlertPreference).filter(
            AlertPreference.user_id == user.id
        ).first()
        
        return IntegrationStatusResponse(
            github={
                "configured": bool(github),
                "enabled": github.enabled if github else False,
                "repository": github.repository if github else None,
                "alert_level": github.alert_level if github else None,
            },
            sentry={
                "configured": bool(sentry),
                "enabled": sentry.enabled if sentry else False,
                "project": sentry.sentry_project_slug if sentry else None,
                "alert_level": sentry.alert_level if sentry else None,
            },
            docker={
                "configured": bool(docker),
                "enabled": docker.enabled if docker else False,
                "registry": docker.docker_registry_url if docker else None,
                "alert_on": docker.alert_on if docker else None,
            },
            firebase={
                "configured": bool(firebase),
                "enabled": firebase.enabled if firebase else False,
                "project_id": firebase.firebase_project_id if firebase else None,
                "alert_level": firebase.alert_level if firebase else None,
            },
            preferences={
                "configured": bool(preferences),
                "channel_id": preferences.channel_id if preferences else None,
                "timezone": preferences.timezone if preferences else None,
                "mute_notifications": preferences.mute_notifications if preferences else False,
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Status check error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Status check failed: {str(e)}"
        )