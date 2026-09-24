from sqlalchemy import create_engine, event, Engine
from app.models.base import Base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

settings = get_settings()

engine = create_engine(
    settings.database_url,
    poolclass=QueuePool,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=True,
    echo=settings.debug,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable foreign keys for PostgreSQL connections"""
    pass


_db_initialized = False


def init_db():
    """Initialize database with all tables"""
    global _db_initialized
    import app.models  # Ensure all models are registered on Base.metadata
    from app.models.base import Base
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    _db_initialized = True
    logger.info("Database tables created successfully")



def get_db() -> Session:
    if not _db_initialized:
        init_db()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


