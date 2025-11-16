# Project: Vigil - Watchful DevOps Monitoring for Zoho Cliq

## Overview
Vigil is a FastAPI-based DevOps monitoring extension for Zoho Cliq that provides real-time alerts for GitHub events, Docker container health, CI/CD pipelines, and production errors (Sentry). All notifications are sent directly to Zoho Cliq channels via webhooks.

## Vigil Architecture
┌─────────────────────────────────────────────────────────┐
│           Zoho Cliq (User Interface)                    │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Bot with / commands (Deluge thin layer)         │   │
│  │ /vigil setup, /vigil status, /vigil docker ps   │   │
│  └──────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────┘
                     │ (calls backend API)
┌────────────────────▼────────────────────────────────────┐
│     Zoho Catalyst (Your FastAPI Backend)               │
│  ┌──────────────────────────────────────────────────┐   │
│  │ • Webhook handlers (GitHub, Docker, Sentry)     │   │
│  │ • Configuration API (/api/configure/*)          │   │
│  │ • Message formatters & Zoho sender              │   │
│  │ • Bot command handlers                          │   │
│  │ • Database storage (configs, integrations)      │   │
│  └──────────────────────────────────────────────────┘   │
└────────┬────────────────┬────────────────┬───────────────┘
         │                │                │
    GitHub API      Docker Registry    Sentry API
         │                │                │
    (Webhooks)       (Webhooks)       (Webhooks)