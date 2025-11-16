from typing import Any, Dict, Optional, List, Union
from pydantic import BaseModel, Field
from datetime import datetime

# ============================================================================
# GitHub Webhook Models
# ============================================================================

class GitHubUser(BaseModel):
    """GitHub user information"""
    login: str
    id: int
    avatar_url: str
    url: str


class GitHubRepository(BaseModel):
    """GitHub repository information"""
    id: int
    name: str
    full_name: str
    private: bool
    html_url: str
    description: Optional[str] = None
    url: str


class GitHubCommit(BaseModel):
    """GitHub commit information"""
    id: str
    tree_id: str
    distinct: bool
    message: str
    timestamp: str
    url: str
    author: GitHubUser
    committer: GitHubUser


class GitHubPushEvent(BaseModel):
    """GitHub Push webhook payload"""
    ref: str = Field(..., description="Branch reference (refs/heads/main)")
    before: str = Field(..., description="Previous commit SHA")
    after: str = Field(..., description="New commit SHA")
    repository: GitHubRepository
    pusher: GitHubUser
    sender: GitHubUser
    commits: List[GitHubCommit]
    head_commit: Optional[GitHubCommit] = None
    created: bool = Field(default=False, description="True if branch was created")
    deleted: bool = Field(default=False, description="True if branch was deleted")
    forced: bool = Field(default=False, description="True if push was forced")


class GitHubPullRequest(BaseModel):
    """GitHub Pull Request information"""
    id: int
    number: int
    state: str  # "open", "closed"
    title: str
    body: Optional[str] = None
    created_at: str
    updated_at: str
    closed_at: Optional[str] = None
    merged_at: Optional[str] = None
    merged: bool = False
    html_url: str
    user: GitHubUser
    head: dict = Field(default_factory=dict, description="Head branch info")
    base: dict = Field(default_factory=dict, description="Base branch info")


class GitHubPullRequestEvent(BaseModel):
    """GitHub Pull Request webhook payload"""
    action: str  # "opened", "closed", "synchronize", "reopened", etc.
    number: int
    pull_request: GitHubPullRequest
    repository: GitHubRepository
    sender: GitHubUser


class GitHubIssue(BaseModel):
    """GitHub Issue information"""
    id: int
    number: int
    state: str  # "open", "closed"
    title: str
    body: Optional[str] = None
    created_at: str
    updated_at: str
    closed_at: Optional[str] = None
    html_url: str
    user: GitHubUser
    labels: List[dict] = Field(default_factory=list)

class GitHubRelease(BaseModel):
    """GitHub Release information"""
    id: int
    tag_name: str
    name: Optional[str] = None
    body: Optional[str] = None
    draft: bool
    prerelease: bool
    created_at: str
    published_at: Optional[str] = None
    html_url: str

class GitHubReleaseEvent(BaseModel):
    """GitHub Release webhook payload"""
    action: str  # "published", "created", "edited", "deleted"
    release: GitHubRelease
    repository: GitHubRepository
    sender: GitHubUser

class GitHubIssueEvent(BaseModel):
    """GitHub Release webhook payload"""
    action: str  # "published", "created", "edited", "deleted"
    release: GitHubRelease
    repository: GitHubRepository
    sender: GitHubUser

# ============================================================================
# Docker Webhook Models
# ============================================================================

class DockerRepository(BaseModel):
    """Docker repository info"""
    name: str
    namespace: Optional[str] = None
    repo_name: Optional[str] = None
    repo_url: Optional[str] = None
    description: Optional[str] = None
    is_official: Optional[bool] = False
    is_private: Optional[bool] = False


class DockerPushEvent(BaseModel):
    """Docker Hub push event"""
    push_data: Dict[str, Any]
    repository: DockerRepository
    sender: Optional[Dict[str, Any]] = None


class DockerBuildEvent(BaseModel):
    """Docker Hub build event"""
    build_data: Dict[str, Any]
    repository: DockerRepository
    push_data: Optional[Dict[str, Any]] = None


class DockerHealthCheckEvent(BaseModel):
    """Docker health check event"""
    status: str
    container_id: str
    container_name: str
    image: str
    timestamp: str
    health_status: str

# ============================================================================
# Sentry Webhook Models
# ============================================================================

class SentryProject(BaseModel):
    """Sentry project info"""
    id: int
    name: str
    slug: str
    platform: Optional[str] = None


class SentryUser(BaseModel):
    """Sentry user info"""
    id: Optional[Union[int, str]] = None  # Can be int or string
    name: Optional[str] = None
    email: Optional[str] = None
    username: Optional[str] = None
    ip_address: Optional[str] = None


class SentryTag(BaseModel):
    """Sentry event tag"""
    key: str
    value: str


class SentryErrorEvent(BaseModel):
    """Sentry error/exception event"""
    id: str
    title: str
    culprit: Optional[str] = None
    level: str  # fatal, error, warning, info, debug
    message: Optional[str] = None
    url: str
    project: SentryProject
    event: Dict[str, Any]
    tags: Optional[Dict[str, str]] = None
    user: Optional[SentryUser] = None
    timestamp: str


class SentryIssueAlert(BaseModel):
    """Sentry issue alert"""
    action: str  # created, resolved, ignored, assigned, etc.
    issue: Dict[str, Any]
    project: SentryProject
    url: str
    description: Optional[str] = None


class SentryWebhookEvent(BaseModel):
    """Generic Sentry webhook event"""
    action: Optional[str] = None
    installation: Optional[Dict[str, Any]] = None
    data: Optional[Dict[str, Any]] = None

# ============================================================================
# Firebase Crashlytics Webhook Models
# ============================================================================

class FirebaseApp(BaseModel):
    """Firebase app information"""
    id: str
    name: str
    platform: str  # "ios", "android"
    bundle_id: Optional[str] = None
    package_name: Optional[str] = None

class FirebaseCrashlyticsCrash(BaseModel):
    """Firebase Crashlytics crash information"""
    id: str
    title: str
    exception_type: str
    reason: str
    stacktrace: Optional[str] = None
    affected_users_count: int
    crashes_count: int
    first_seen_at: str
    last_seen_at: str
    severity: str  # "fatal", "error", "warning"

class FirebaseCrashlyticsSession(BaseModel):
    """Firebase session information"""
    app: FirebaseApp
    crash: FirebaseCrashlyticsCrash
    user_count: int
    session_count: int

class FirebaseCrashlyticsEvent(BaseModel):
    """Firebase Crashlytics webhook payload"""
    incident_id: str
    app: FirebaseApp
    crash: FirebaseCrashlyticsCrash
    link: str  # Link to Firebase Console
    event_type: str  # "new_crash_group", "regressed_crash_group", "velocity_alert"
    timestamp: str

class FirebaseCrashlyticsAlertEvent(BaseModel):
    """Firebase Crashlytics alert event"""
    alert_type: str  # "new_fatal_issue", "new_non_fatal_issue", "regression", "velocity"
    app: FirebaseApp
    crash: FirebaseCrashlyticsCrash
    message: Optional[str] = None
    link: str
    timestamp: str
