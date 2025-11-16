from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.webhooks import (
    FirebaseCrashlyticsEvent,
    FirebaseCrashlyticsAlertEvent,
)
from app.services.zoho_cliq import zoho_client
from app.db.database import get_db
from app.db.models import FirebaseIntegration, AlertLog

router = APIRouter()


@router.post("/firebase", tags=["Firebase"])
async def firebase_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Firebase Crashlytics webhook endpoint
    Receives crash events, alerts, and regressions from Firebase Console
    Reads user config from database
    """
    try:
        payload = await request.json()
        
        # Determine event type from payload structure
        if "incident_id" in payload and "event_type" in payload:
            event = FirebaseCrashlyticsEvent(**payload)
            await send_crashlytics_alert(event, db)
            return {"status": "received", "event_type": "crashlytics_event", "incident_type": payload.get("event_type")}
        
        elif "alert_type" in payload and "app" in payload:
            event = FirebaseCrashlyticsAlertEvent(**payload)
            await send_alert_event(event, db)
            return {"status": "received", "event_type": "alert_event", "alert_type": payload.get("alert_type")}
        
        else:
            return {"status": "ignored", "message": "Unknown Firebase event type"}
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {str(e)}")
    except Exception as e:
        print(f"❌ Firebase webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def send_crashlytics_alert(event: FirebaseCrashlyticsEvent, db: Session):
    """Format and send Firebase Crashlytics event to Zoho - READ FROM DB"""
    app_name = event.app.name
    platform = event.app.platform.upper()
    crash_title = event.crash.title
    exception_type = event.crash.exception_type
    event_type = event.event_type
    
    # Find user config from DB
    firebase_config = db.query(FirebaseIntegration).filter(
        FirebaseIntegration.firebase_project_id == event.app.id
    ).first()
    
    if not firebase_config or not firebase_config.enabled:
        print(f"⚠️  No active Firebase config for {app_name}")
        return
    
    print(f"\n🔥 Firebase Crashlytics Event")
    print(f"   App: {app_name} ({platform})")
    print(f"   Event Type: {event_type}")
    print(f"   Exception: {exception_type}")
    
    event_emoji = {
        "new_crash_group": "🆕",
        "regressed_crash_group": "📈",
        "velocity_alert": "⚠️"
    }
    
    severity_map = {
        "new_crash_group": "error",
        "regressed_crash_group": "error",
        "velocity_alert": "warning"
    }
    
    emoji = event_emoji.get(event_type, "🔥")
    severity = severity_map.get(event_type, "error")
    
    event_text = event_type.replace("_", " ").title()
    alert_title = f"{emoji} {event_text}: {exception_type}"
    description = f"Crash detected in {app_name} ({platform})\n\n{crash_title}"
    
    metadata = {
        "App": app_name,
        "Platform": platform,
        "Exception": exception_type,
        "Event Type": event_text,
        "Affected Users": str(event.crash.affected_users_count),
        "Total Crashes": str(event.crash.crashes_count),
    }
    
    actions = [
        {"label": "View in Firebase Console", "url": event.link}
    ]
    
    result = await zoho_client.send_alert(
        title=alert_title,
        description=description,
        severity=severity,
        metadata=metadata,
        actions=actions,
        text_fallback=f"{emoji} {event_text} in {app_name}: {exception_type}"
    )
    
    # Log alert
    alert_log = AlertLog(
        user_id=firebase_config.user_id,
        alert_type="firebase",
        event_type="crashlytics",
        title=alert_title,
        severity=severity,
        message=description,
        source_id=exception_type
    )
    db.add(alert_log)
    db.commit()
    
    print(f"✅ Firebase crashlytics alert sent and logged\n")


async def send_alert_event(event: FirebaseCrashlyticsAlertEvent, db: Session):
    """Format and send Firebase Crashlytics alert event to Zoho - READ FROM DB"""
    app_name = event.app.name
    platform = event.app.platform.upper()
    alert_type = event.alert_type
    exception_type = event.crash.exception_type
    
    # Find user config from DB
    firebase_config = db.query(FirebaseIntegration).filter(
        FirebaseIntegration.firebase_project_id == event.app.id
    ).first()
    
    if not firebase_config or not firebase_config.enabled:
        print(f"⚠️  No active Firebase config for {app_name}")
        return
    
    print(f"\n🔥 Firebase Alert Event")
    print(f"   App: {app_name} ({platform})")
    print(f"   Alert Type: {alert_type}")
    print(f"   Exception: {exception_type}")
    
    alert_emoji = {
        "new_fatal_issue": "🔴",
        "new_non_fatal_issue": "⚠️",
        "regression": "📈",
        "velocity": "🚨"
    }
    
    severity_map = {
        "new_fatal_issue": "critical",
        "new_non_fatal_issue": "warning",
        "regression": "error",
        "velocity": "error"
    }
    
    emoji = alert_emoji.get(alert_type, "🔥")
    severity = severity_map.get(alert_type, "error")
    
    alert_text = alert_type.replace("_", " ").title()
    alert_title = f"{emoji} {alert_text}: {app_name}"
    description = f"{event.crash.title}\n\nException: {exception_type}"
    
    metadata = {
        "App": app_name,
        "Platform": platform,
        "Alert Type": alert_text,
        "Exception Type": exception_type,
        "Affected Users": str(event.crash.affected_users_count),
    }
    
    actions = [
        {"label": "View in Firebase Console", "url": event.link}
    ]
    
    result = await zoho_client.send_alert(
        title=alert_title,
        description=description,
        severity=severity,
        metadata=metadata,
        actions=actions,
        text_fallback=f"{emoji} {alert_text}: {exception_type} in {app_name}"
    )
    
    # Log alert
    alert_log = AlertLog(
        user_id=firebase_config.user_id,
        alert_type="firebase",
        event_type="alert",
        title=alert_title,
        severity=severity,
        message=description,
        source_id=alert_type
    )
    db.add(alert_log)
    db.commit()
    
    print(f"✅ Firebase alert event sent and logged\n")