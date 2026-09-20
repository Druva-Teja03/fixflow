import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from backend.app.config import settings

logger = logging.getLogger("fixflow.database")

# Configure PyMySQL SSL if DB_SSL is enabled (for hosted/cloud MySQL)
connect_args = {}
if settings.DB_SSL:
    ssl_config = {}
    if settings.DB_SSL_CA:
        ssl_config["ca"] = settings.DB_SSL_CA
    connect_args["ssl"] = ssl_config

# Create SQLAlchemy engine for MySQL with PyMySQL driver
# pool_pre_ping=True prevents stale connection drops
# pool_recycle=3600 recycles connections every hour
engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=(settings.APP_ENV == "debug"),
)

# Session factory for handling requests
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base for ORM models
Base = declarative_base()


def get_db():
    """
    FastAPI dependency that provides a transactional database session per request.
    Automatically closes the session when the request completes.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> bool:
    """
    Test connectivity to the MySQL database server.
    Returns True if successful, False otherwise.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
        return True
    except Exception as exc:
        logger.error(f"Database connection check failed: {exc}")
        return False
