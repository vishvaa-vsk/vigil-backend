from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.webhooks import (
    SentryErrorEvent,
    SentryIssueAlert,
)
from app.services.zoho_cliq import zoho_client
from app.db.database import get_db
from app.db.models import SentryIntegration, AlertLog

router = APIRouter()


@router.post("/sentry", tags=["Sentry"])
async def sentry_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Sentry webhook endpoint
    Receives error events, issue alerts, and resolution updates from Sentry
    Reads user config from database
    """
    try:
        payload = await request.json()
        
        # Determine event type from payload structure
        if "issue" in payload and "action" in payload:
            # Issue alert (created, resolved, assigned, etc.)
            event = SentryIssueAlert(**payload)
            await send_issue_alert(event, db)
            return {"status": "received", "event_type": "issue_alert", "action": payload.get("action")}
        
        elif "id" in payload and "title" in payload and "level" in payload:
            # Error event
            event = SentryErrorEvent(**payload)
            await send_error_alert(event, db)
            return {"status": "received", "event_type": "error_event"}
        
        else:
            return {"status": "ignored", "message": "Unknown Sentry event type"}
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {str(e)}")
    except Exception as e:
        print(f"❌ Sentry webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def send_error_alert(event: SentryErrorEvent, db: Session):
    """Format and send Sentry error event to Zoho - READ FROM DB"""
    error_id = event.id
    title = event.title
    level = event.level
    culprit = event.culprit or "unknown"
    project = event.project.name
    url = event.url
    
    # Find user config from DB
    sentry_config = db.query(SentryIntegration).filter(
        SentryIntegration.sentry_project_slug == event.project.slug
    ).first()
    
    if not sentry_config or not sentry_config.enabled:
        print(f"⚠️  No active Sentry config for {project}")
        return
    
    print(f"\n🚨 Sentry Error Event")
    print(f"   Project: {project}")
    print(f"   Level: {level}")
    print(f"   Title: {title}")
    print(f"   Culprit: {culprit}")
    
    level_emoji = {
        "fatal": "🔴",
        "error": "❌",
        "warning": "⚠️",
        "info": "ℹ️",
        "debug": "🐛"
    }
    
    severity_map = {
        "fatal": "critical",
        "error": "error",
        "warning": "warning",
        "info": "info",
        "debug": "info"
    }
    
    emoji = level_emoji.get(level, "⚠️")
    severity = severity_map.get(level, "warning")
    
    alert_title = f"{emoji} {level.upper()}: {title}"
    description = f"New error detected in production\n\nCulprit: {culprit}\nProject: {project}"
    
    metadata = {
        "Error ID": error_id,
        "Level": level.upper(),
        "Project": project,
        "Culprit": culprit,
    }
    
    if event.user and event.user.username:
        metadata["Affected User"] = event.user.username
    
    if event.tags:
        tags_str = ", ".join([f"{k}: {v}" for k, v in list(event.tags.items())[:3]])
        metadata["Tags"] = tags_str
    
    actions = [
        {"label": "View in Sentry", "url": url}
    ]
    
    result = await zoho_client.send_alert(
        title=alert_title,
        description=description,
        severity=severity,
        metadata=metadata,
        actions=actions,
        text_fallback=f"{emoji} {level.upper()}: {title} in {project}"
    )
    
    # Log alert
    alert_log = AlertLog(
        user_id=sentry_config.user_id,
        alert_type="sentry",
        event_type="error",
        title=alert_title,
        severity=severity,
        message=description,
        source_id=error_id
    )
    db.add(alert_log)
    db.commit()
    
    print(f"✅ Sentry error alert sent and logged\n")


async def send_issue_alert(event: SentryIssueAlert, db: Session):
    """Format and send Sentry issue alert to Zoho - READ FROM DB"""
    action = event.action
    issue = event.issue
    project = event.project.name
    url = event.url
    
    # Find user config from DB
    sentry_config = db.query(SentryIntegration).filter(
        SentryIntegration.sentry_project_slug == event.project.slug
    ).first()
    
    if not sentry_config or not sentry_config.enabled:
        print(f"⚠️  No active Sentry config for {project}")
        return
    
    print(f"\n🚨 Sentry Issue Event")
    print(f"   Action: {action}")
    print(f"   Project: {project}")
    print(f"   Issue: {issue.get('title', 'Unknown')}")
    
    issue_id = issue.get("id", "N/A")
    issue_title = issue.get("title", "Unknown issue")
    issue_level = issue.get("level", "error")
    
    action_emoji = {
        "created": "🆕",
        "resolved": "✅",
        "ignored": "🔇",
        "assigned": "👤",
        "regressed": "📈",
        "reopened": "🔄"
    }
    
    severity_map = {
        "created": "error",
        "resolved": "info",
        "ignored": "warning",
        "assigned": "info",
        "regressed": "error",
        "reopened": "warning"
    }
    
    emoji = action_emoji.get(action, "🔔")
    severity = severity_map.get(action, "warning")
    
    action_text = action.replace("_", " ").title()
    alert_title = f"{emoji} Issue {action_text}: {issue_title}"
    description = f"Issue {action} in {project}\n\nLevel: {issue_level}"
    
    metadata = {
        "Issue ID": str(issue_id),
        "Action": action_text,
        "Project": project,
        "Level": issue_level.upper(),
        "Status": issue.get("status", "unresolved").upper(),
    }
    
    if issue.get("assignedTo"):
        assignee = issue["assignedTo"].get("name", issue["assignedTo"].get("email", "Unknown"))
        metadata["Assigned To"] = assignee
    
    if issue.get("count"):
        metadata["Event Count"] = str(issue["count"])
    
    actions = [
        {"label": "View Issue", "url": url}
    ]
    
    result = await zoho_client.send_alert(
        title=alert_title,
        description=description,
        severity=severity,
        metadata=metadata,
        actions=actions,
        text_fallback=f"{emoji} Issue {action}: {issue_title}"
    )
    
    # Log alert
    alert_log = AlertLog(
        user_id=sentry_config.user_id,
        alert_type="sentry",
        event_type="issue",
        title=alert_title,
        severity=severity,
        message=description,
        source_id=str(issue_id)
    )
    db.add(alert_log)
    db.commit()
    
    print(f"✅ Sentry issue alert sent and logged\n")