from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.webhooks import (
    DockerPushEvent,
    DockerBuildEvent,
    DockerHealthCheckEvent,
)
from app.services.zoho_cliq import zoho_client
from app.db.database import get_db
from app.db.models import DockerIntegration, AlertLog

router = APIRouter()


@router.post("/docker", tags=["Docker"])
async def docker_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Docker webhook endpoint
    Receives push, build, and health check events from Docker Hub
    Reads user config from database
    """
    try:
        payload = await request.json()
        
        # Extract repo name to find config
        repo_name = payload.get("repository", {}).get("name", "")
        
        # Determine event type from payload structure
        if "build_data" in payload and "repository" in payload:
            event = DockerBuildEvent(**payload)
            await send_build_alert(event, db, repo_name)
            return {"status": "received", "event_type": "build"}
        
        elif "push_data" in payload and "repository" in payload:
            event = DockerPushEvent(**payload)
            await send_push_alert(event, db, repo_name)
            return {"status": "received", "event_type": "push"}
        
        elif "status" in payload and "container_id" in payload:
            event = DockerHealthCheckEvent(**payload)
            await send_health_alert(event, db)
            return {"status": "received", "event_type": "health_check"}
        
        else:
            return {"status": "ignored", "message": "Unknown Docker event type"}
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {str(e)}")
    except Exception as e:
        print(f"❌ Docker webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def send_push_alert(event: DockerPushEvent, db: Session, repo_name: str):
    """Format and send Docker push event to Zoho - READ FROM DB"""
    repo = event.repository.name
    tag = event.push_data.get("tag", "latest")
    pusher = event.push_data.get("pushed_by", "unknown")
    
    # Find user config from DB
    docker_config = db.query(DockerIntegration).filter(
        DockerIntegration.docker_registry_url.ilike(f"%{repo}%")
    ).first()
    
    if not docker_config or not docker_config.enabled:
        print(f"⚠️  No active Docker config for {repo}")
        return
    
    print(f"\n🐳 Docker Push Event")
    print(f"   Repository: {repo}")
    print(f"   Tag: {tag}")
    print(f"   Pusher: {pusher}")
    
    title = f"🐳 Docker Image Pushed: {repo}:{tag}"
    description = f"New image pushed to Docker Hub\n\nPushed by: {pusher}"
    
    metadata = {
        "Repository": repo,
        "Tag": tag,
        "Pusher": pusher,
    }
    
    actions = [
        {"label": "View on Docker Hub", "url": f"https://hub.docker.com/r/{repo}/tags"}
    ]
    
    result = await zoho_client.send_alert(
        title=title,
        description=description,
        severity="info",
        metadata=metadata,
        actions=actions,
        text_fallback=f"🐳 New Docker image: {repo}:{tag} pushed by {pusher}"
    )
    
    # Log alert
    alert_log = AlertLog(
        user_id=docker_config.user_id,
        alert_type="docker",
        event_type="push",
        title=title,
        severity="info",
        message=description,
        source_id=f"{repo}:{tag}"
    )
    db.add(alert_log)
    db.commit()
    
    print(f"✅ Docker push alert sent and logged\n")


async def send_build_alert(event: DockerBuildEvent, db: Session, repo_name: str):
    """Format and send Docker build event to Zoho - READ FROM DB"""
    repo = event.repository.name
    build_status = event.build_data.get("status", "unknown")
    build_id = event.build_data.get("build_id", "N/A")
    tag = event.build_data.get("tag", "latest")
    
    # Find user config from DB
    docker_config = db.query(DockerIntegration).filter(
        DockerIntegration.docker_registry_url.ilike(f"%{repo}%")
    ).first()
    
    if not docker_config or not docker_config.enabled:
        print(f"⚠️  No active Docker config for {repo}")
        return
    
    print(f"\n🔨 Docker Build Event")
    print(f"   Repository: {repo}")
    print(f"   Status: {build_status}")
    print(f"   Build ID: {build_id}")
    
    status_emoji = {
        "Success": "✅",
        "Failed": "❌",
        "Building": "🔨",
        "Pending": "⏳"
    }
    
    emoji = status_emoji.get(build_status, "📦")
    severity = "info" if build_status == "Success" else "error"
    
    title = f"{emoji} Docker Build {build_status}: {repo}:{tag}"
    description = f"Docker build {build_status.lower()}\n\nBuild ID: {build_id}"
    
    metadata = {
        "Repository": repo,
        "Tag": tag,
        "Build Status": build_status,
        "Build ID": build_id,
    }
    
    actions = [
        {"label": "View Build", "url": f"https://hub.docker.com/r/{repo}/builds"}
    ]
    
    result = await zoho_client.send_alert(
        title=title,
        description=description,
        severity=severity,
        metadata=metadata,
        actions=actions,
        text_fallback=f"{emoji} Docker build {build_status}: {repo}:{tag}"
    )
    
    # Log alert
    alert_log = AlertLog(
        user_id=docker_config.user_id,
        alert_type="docker",
        event_type="build",
        title=title,
        severity=severity,
        message=description,
        source_id=build_id
    )
    db.add(alert_log)
    db.commit()
    
    print(f"✅ Docker build alert sent and logged\n")


async def send_health_alert(event: DockerHealthCheckEvent, db: Session):
    """Format and send Docker health check event to Zoho"""
    container_name = event.container_name
    container_id = event.container_id[:12]
    health_status = event.health_status
    image = event.image
    
    print(f"\n💊 Docker Health Check Event")
    print(f"   Container: {container_name}")
    print(f"   Status: {health_status}")
    print(f"   Image: {image}")
    
    status_emoji = {
        "healthy": "✅",
        "unhealthy": "❌",
        "starting": "🔄"
    }
    
    emoji = status_emoji.get(health_status, "⚠️")
    severity = "error" if health_status == "unhealthy" else "warning" if health_status == "starting" else "info"
    
    title = f"{emoji} Container Health: {container_name} is {health_status.upper()}"
    description = f"Health check status changed\n\nContainer: {container_name}\nImage: {image}"
    
    metadata = {
        "Container": container_name,
        "Container ID": container_id,
        "Health Status": health_status,
        "Image": image,
    }
    
    result = await zoho_client.send_alert(
        title=title,
        description=description,
        severity=severity,
        metadata=metadata,
        actions=None,
        text_fallback=f"{emoji} Container {container_name} is {health_status}"
    )
    
    print(f"✅ Docker health alert sent\n")