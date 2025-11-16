from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db.database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    #startup
    print("🚀 Vigil Backend starting up...")
    print(f"Debug mode: {settings.debug}")
    print(f"Environment: {settings.environment}")
    print(f"Server: {settings.server_host}:{settings.server_port}")
    print(f"Database: {settings.database_url}")

    await init_db()
    print("✅ Database initialized")

    yield

    #shutdown
    print("🛑 Vigil Backend shutting down...")

app = FastAPI(
    title="Vigil - DevOps Monitoring Tool for Zoho Cliq",
    description="Real-time alerts for GitHub, Docker, and Sentry in Zoho Cliq",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health Check Endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Vigil Backend",
        "version": "1.0.0"
    }

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Vigil - DevOps Monitoring Tool for Zoho Cliq",
        "docs": "/docs" if settings.debug else "Not available in production",
        "health": "/health"
    }

from app.routers import github ,docker, sentry, crashlytics, configure

app.include_router(configure.router, prefix="/api/configure", tags=["Configuration"])
app.include_router(github.router, prefix="/webhooks", tags=["GitHub Webhooks"])
app.include_router(docker.router, prefix="/webhooks", tags=["Docker Webhooks"])
app.include_router(sentry.router, prefix="/webhooks", tags=["Sentry Webhooks"])
app.include_router(crashlytics.router, prefix="/webhooks", tags=["Firebase Webhooks"])


# Error handling
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    print(f"❌ Unhandled error: {str(exc)}")
    return {
        "error": "Internal server error",
        "message": str(exc) if settings.debug else "An error occurred"
    }

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )