import hmac
import hashlib
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.webhooks import (
    GitHubPushEvent,
    GitHubPullRequestEvent,
    GitHubIssueEvent,
    GitHubReleaseEvent,
)
from app.services.zoho_cliq import zoho_client
from app.db.database import get_db
from app.db.models import GitHubIntegration, AlertLog
from app.core.config import settings

router = APIRouter()

def verify_github_signature(payload: bytes, signature: str) -> bool:
    """
    Verify GitHub webhook signature for security
    GitHub sends X-Hub-Signature-256 header with HMAC-SHA256
    """
    if not settings.github_webhook_secret:
        print("⚠️  GitHub webhook secret not configured, skipping verification")
        return True
    
    expected_signature = "sha256=" + hmac.new(
        settings.github_webhook_secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, signature)


@router.post("/github", tags=["GitHub"])
async def github_webhook(request: Request, db: Session = Depends(get_db)):
    """
    GitHub webhook endpoint
    Receives push, PR, issue, and release events
    """
    try:
        # Get raw body for signature verification
        body = await request.body()
        
        # Verify signature if secret is configured
        signature = request.headers.get("X-Hub-Signature-256")
        if signature:
            if not verify_github_signature(body, signature):
                print("❌ Invalid GitHub webhook signature")
                raise HTTPException(status_code=401, detail="Invalid signature")
            print("✅ GitHub webhook signature verified")


        payload = await request.json()
        event_type = request.headers.get("X-GitHub-Event")
        
        if not event_type:
            raise HTTPException(status_code=400, detail="Missing X-GitHub-Event header")
        
        repo_full_name = payload.get("repository", {}).get("full_name","")
        
        # Route events based on type
        if event_type == "push":
            event = GitHubPushEvent(**payload)
            await send_push_alert(event,db,repo_full_name)
            return {"status": "received", "event_type": "push"}
        
        elif event_type == "pull_request":
            event = GitHubPullRequestEvent(**payload)
            await send_pr_alert(event,db,repo_full_name)
            return {"status": "received", "event_type": "pull_request"}
        
        elif event_type == "issues":
            event = GitHubIssueEvent(**payload)
            await send_issue_alert(event,db,repo_full_name)
            return {"status": "received", "event_type": "issues"}
        
        elif event_type == "release":
            event = GitHubReleaseEvent(**payload)
            await send_release_alert(event,db,repo_full_name)
            return {"status": "received", "event_type": "release"}
        
        else:
            return {"status": "ignored", "event_type": event_type}
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {str(e)}")
    except Exception as e:
        print(f"❌ GitHub webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def send_push_alert(event: GitHubPushEvent, db: Session, repo_full_name: str):
    """Format and send push event to Zoho - READ FROM DB"""
    branch = event.ref.split("/")[-1]
    repo = event.repository.full_name
    pusher = event.pusher.login
    commit_count = len(event.commits)

    # Find user config from DB
    github_config = db.query(GitHubIntegration).filter(
        GitHubIntegration.repository == repo_full_name
    ).first()
    
    if not github_config:
        print(f"⚠️  No GitHub config found for {repo_full_name}, ignoring webhook")
        return
    
    if not github_config.enabled:
        print(f"⚠️  GitHub config disabled for {repo_full_name}")
        return
    
    print(f"\n📤 GitHub Push Event")
    print(f"   Repository: {repo}")
    print(f"   Branch: {branch}")
    print(f"   Pusher: {pusher}")
    print(f"   Commits: {commit_count}")
    print(f"   Alert Level: {github_config.alert_level}")

    title = f"📤 Push to {repo}/{branch}"
    description = f"{pusher} pushed {commit_count} commit(s)\n\n"
    
    # Add commit messages
    for commit in event.commits:
        description += f"• {commit.message}\n"
    
    metadata = {
        "Repository": repo,
        "Branch": branch,
        "Pusher": pusher,
        "Commits": str(commit_count),
        "URL": event.repository.html_url
    }
    
    actions = [
        {"label": "View on GitHub", "url": event.repository.html_url}
    ]
    
    result = await zoho_client.send_alert(
        title=title,
        description=description,
        severity="info",
        metadata=metadata,
        actions=actions,
        text_fallback=f"📤 {pusher} pushed {commit_count} commits to {repo}/{branch}"
    )
    
    # Log alert in database
    alert_log = AlertLog(
        user_id=github_config.user_id,
        alert_type="github",
        event_type="push",
        title=title,
        severity="info",
        message=description,
        source_id=event.after  # Commit SHA
    )
    db.add(alert_log)
    db.commit()
    
    print(f"✅ Push alert sent and logged")


async def send_pr_alert(event: GitHubPullRequestEvent, db: Session, repo_full_name: str):
    """Format and send PR event to Zoho - READ FROM DB"""
    pr = event.pull_request
    action = event.action
    repo = event.repository.full_name
    
    # Find user config from DB
    github_config = db.query(GitHubIntegration).filter(
        GitHubIntegration.repository == repo_full_name
    ).first()
    
    if not github_config or not github_config.enabled:
        print(f"⚠️  No active GitHub config for {repo_full_name}")
        return
    
    print(f"\n📋 GitHub PR Event")
    print(f"   Repository: {repo}")
    print(f"   PR #{pr.number}: {pr.title}")
    print(f"   Action: {action}")
    
    action_emoji = {
        "opened": "🆕",
        "closed": "❌",
        "merged": "✅",
        "synchronize": "🔄",
        "reopened": "🔁"
    }
    
    emoji = action_emoji.get(action, "📋")
    title = f"{emoji} PR #{pr.number} {action.title()}"
    description = f"**{pr.title}**\n\nBy: {pr.user.login}"
    
    metadata = {
        "Repository": repo,
        "Action": action,
        "State": pr.state,
        "Author": pr.user.login
    }
    
    actions = [
        {"label": "View PR", "url": pr.html_url}
    ]
    
    result = await zoho_client.send_alert(
        title=title,
        description=description,
        severity="warning" if action in ["opened", "synchronize"] else "info",
        metadata=metadata,
        actions=actions,
        text_fallback=f"{emoji} PR #{pr.number} {action}: {pr.title}"
    )
    
    # Log alert
    alert_log = AlertLog(
        user_id=github_config.user_id,
        alert_type="github",
        event_type="pull_request",
        title=title,
        severity="warning" if action in ["opened", "synchronize"] else "info",
        message=description,
        source_id=str(pr.number)
    )
    db.add(alert_log)
    db.commit()
    
    print(f"✅ PR alert sent and logged")


async def send_issue_alert(event: GitHubIssueEvent, db: Session, repo_full_name: str):
    """Format and send issue event to Zoho - READ FROM DB"""
    issue = event.issue
    action = event.action
    repo = event.repository.full_name
    
    # Find user config from DB
    github_config = db.query(GitHubIntegration).filter(
        GitHubIntegration.repository == repo_full_name
    ).first()
    
    if not github_config or not github_config.enabled:
        print(f"⚠️  No active GitHub config for {repo_full_name}")
        return
    
    print(f"\n🔖 GitHub Issue Event")
    print(f"   Repository: {repo}")
    print(f"   Issue #{issue.number}: {issue.title}")
    print(f"   Action: {action}")
    
    action_emoji = {
        "opened": "🆕",
        "closed": "✅",
        "reopened": "🔁",
        "labeled": "🏷️",
        "assigned": "👤"
    }
    
    emoji = action_emoji.get(action, "📌")
    title = f"{emoji} Issue #{issue.number} {action.title()}"
    description = f"**{issue.title}**\n\nBy: {issue.user.login}"
    
    metadata = {
        "Repository": repo,
        "Action": action,
        "State": issue.state,
        "Author": issue.user.login
    }
    
    actions = [
        {"label": "View Issue", "url": issue.html_url}
    ]
    
    result = await zoho_client.send_alert(
        title=title,
        description=description,
        severity="error" if action == "opened" else "info",
        metadata=metadata,
        actions=actions,
        text_fallback=f"{emoji} Issue #{issue.number} {action}: {issue.title}"
    )
    
    # Log alert
    alert_log = AlertLog(
        user_id=github_config.user_id,
        alert_type="github",
        event_type="issue",
        title=title,
        severity="error" if action == "opened" else "info",
        message=description,
        source_id=str(issue.number)
    )
    db.add(alert_log)
    db.commit()
    
    print(f"✅ Issue alert sent and logged")


async def send_release_alert(event: GitHubReleaseEvent, db: Session, repo_full_name: str):
    """Format and send release event to Zoho - READ FROM DB"""
    release = event.release
    action = event.action
    repo = event.repository.full_name
    
    # Find user config from DB
    github_config = db.query(GitHubIntegration).filter(
        GitHubIntegration.repository == repo_full_name
    ).first()
    
    if not github_config or not github_config.enabled:
        print(f"⚠️  No active GitHub config for {repo_full_name}")
        return
    
    print(f"\n🎉 GitHub Release Event")
    print(f"   Repository: {repo}")
    print(f"   Release: {release.tag_name}")
    print(f"   Action: {action}")
    
    title = f"🎉 Release {release.tag_name} {action.title()}"
    description = f"**{release.name or release.tag_name}**\n\nBy: {release.author.login}"
    
    if release.body:
        description += f"\n\n{release.body[:200]}..."
    
    metadata = {
        "Repository": repo,
        "Version": release.tag_name,
        "Author": release.author.login,
        "Draft": str(release.draft),
        "Prerelease": str(release.prerelease)
    }
    
    actions = [
        {"label": "View Release", "url": release.html_url}
    ]
    
    result = await zoho_client.send_alert(
        title=title,
        description=description,
        severity="info",
        metadata=metadata,
        actions=actions,
        text_fallback=f"🎉 Release {release.tag_name} {action}"
    )
    
    # Log alert
    alert_log = AlertLog(
        user_id=github_config.user_id,
        alert_type="github",
        event_type="release",
        title=title,
        severity="info",
        message=description,
        source_id=release.tag_name
    )
    db.add(alert_log)
    db.commit()
    
    print(f"✅ Release alert sent and logged")