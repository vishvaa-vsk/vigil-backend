# Vigil Backend Implementation Plan

## Project Overview

Vigil is a FastAPI-based DevOps monitoring extension for Zoho Cliq that provides real-time alerts for GitHub events, Docker container health, CI/CD pipelines, and production errors (Sentry). All notifications are sent directly to Zoho Cliq channels via webhooks.

## Current State

- **Status:** Early stage skeleton with directory structure created but no implementation
- **Available:** Dependencies configured in `pyproject.toml`, environment variables in `.env`, project structure in place
- **Missing:** All business logic implementation across config, models, services, formatters, and routers

## Architecture Flow

```
Incoming webhooks (GitHub/Docker/Sentry)
    ↓
FastAPI routers validate & receive
    ↓
Formatters transform event data to Zoho Cliq format
    ↓
Zoho Cliq service sends formatted messages to channels
```

## Implementation Order

### 1. Configuration Management

**File:** `app/core/config.py`
**Purpose:** Load and validate environment variables from `.env` using Pydantic Settings
**Requirements:**

- Load `ZOHO_CLIQ_WEBHOOK_URL`, `ZOHO_CLIQ_TOKEN`, `GITHUB_WEBHOOK_SECRET`, `SENTRY_DSN`
- Load `SERVER_HOST`, `SERVER_PORT`, `DEBUG`
- Provide typed access to all configuration values

### 2. Data Models

**File:** `app/models/webhooks.py`
**Purpose:** Define Pydantic models for incoming webhook payloads from GitHub, Docker, and Sentry
**Requirements:**

- GitHub webhook model for repository events (push, PR, issues, etc.)
- Docker webhook model for container/registry events
- Sentry webhook model for error alerts
- Ensure models handle optional/required fields appropriately

### 3. FastAPI Application Setup

**File:** `main.py`
**Purpose:** Initialize and configure the main FastAPI application
**Requirements:**

- Create FastAPI instance with title and description
- Register all routers (github, docker, sentry)
- Include health check endpoint
- Configure CORS if needed for local testing
- Run with Uvicorn on configured host/port

### 4. Zoho Cliq Service

**File:** `app/services/zoho_cliq.py`
**Purpose:** HTTP client to send formatted messages to Zoho Cliq channels
**Requirements:**

- Use webhook URL and token from configuration
- Send formatted message objects to Zoho Cliq API
- Handle HTTP errors gracefully with logging
- Return success/failure status

### 5. Message Formatters

**Files:**

- `app/formatters/github_formatter.py`
- `app/formatters/docker_formatter.py`
- `app/formatters/sentry_formatter.py`

**Purpose:** Transform raw webhook events into user-friendly Zoho Cliq messages
**Requirements:**

- Extract relevant data from each event type
- Format as Zoho Cliq message JSON structure
- Include actionable information (event type, status, links, timestamps)
- Handle different event subtypes (e.g., push vs PR for GitHub)

### 6. Webhook Endpoints

**Files:**

- `app/routers/github.py` — POST endpoint for GitHub events
- `app/routers/docker.py` — POST endpoint for Docker events
- `app/routers/sentry.py` — POST endpoint for Sentry events

**Purpose:** Receive and process incoming webhooks
**Requirements:**

- Validate webhook signatures (especially GitHub's HMAC signature)
- Parse and validate payload against models
- Call appropriate formatter
- Call Zoho Cliq service to send message
- Return appropriate HTTP responses (200 OK, 400 Bad Request, 500 Server Error)
- Include error handling and logging

## Key Considerations

### Security

- **GitHub Webhook Verification:** Verify HMAC signature using `GITHUB_WEBHOOK_SECRET`
- **Token Protection:** Keep `ZOHO_CLIQ_TOKEN` secure, don't log it
- **Input Validation:** Validate all incoming payloads against models

### Message Format

- Zoho Cliq expects specific JSON structure—formatters must match this
- Messages should be actionable and clear (event type, status, relevant links)
- Consider color coding or emoji for quick visual scanning

### Error Handling

- Each endpoint should handle invalid payloads gracefully
- Log errors with context but avoid exposing sensitive data
- Return appropriate HTTP status codes
- Implement retry logic if Zoho Cliq service is temporarily unavailable

### Testing

- Use `pytest` and `pytest-asyncio` for unit tests
- Test webhook validation logic
- Test message formatting
- Mock external API calls (Zoho Cliq)

## Dependencies Already Available

- `fastapi>=0.121.2` — Web framework
- `uvicorn>=0.38.0` — ASGI server
- `pydantic>=2.12.4` & `pydantic-settings>=2.12.0` — Data validation
- `requests>=2.32.5` — HTTP client
- `python-dotenv>=1.2.1` — Environment variable loading
- `pytest>=9.0.1` & `pytest-asyncio>=1.3.0` — Testing

## Environment Variables Ready

```
ZOHO_CLIQ_WEBHOOK_URL=<webhook_url>
ZOHO_CLIQ_TOKEN=<token>
GITHUB_WEBHOOK_SECRET=<to_be_filled>
SENTRY_DSN=<to_be_filled>
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
DEBUG=true
```

## Next Steps

1. Confirm implementation order preference
2. Start with Configuration Management
3. Build each component in order, testing as we go
4. Document API endpoints once complete
