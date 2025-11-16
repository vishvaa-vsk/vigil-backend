from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Database URL configuration
database_url = settings.database_url

# SQLAlchemy engine configuration for PostgreSQL
engine = create_engine(
    database_url,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=20,  # Connection pool size
    max_overflow=40,  # Max overflow connections
    echo=settings.debug,  # Log SQL queries in debug mode
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Base for all models
Base = declarative_base()


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def init_db():
    """Initialize database - create all tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ PostgreSQL tables created/verified")


async def drop_db():
    """Drop all tables - use with caution!"""
    Base.metadata.drop_all(bind=engine)
    print("⚠️ All tables dropped")