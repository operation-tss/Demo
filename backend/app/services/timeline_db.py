import os
import sys
import logging
from typing import Generator, Optional
from contextlib import contextmanager

logger = logging.getLogger("timeline_db")

try:
    from sqlmodel import create_engine, Session
    from sqlalchemy import text
except ImportError as e:
    logger.error(f"SQLModel / SQLAlchemy could not be imported: {e}")
    create_engine = None
    Session = None
    text = None

# Default connection string matching Healthcare Connect MSSQL instance
DEFAULT_DATABASE_URL = (
    "mssql+pyodbc:///?odbc_connect="
    "DRIVER%3D%7BODBC+Driver+17+for+SQL+Server%7D%3B"
    "SERVER%3D.%3B"
    "DATABASE%3DHealthCare_connect%3B"
    "Trusted_Connection%3Dyes%3B"
    "TrustServerCertificate%3Dyes%3B"
)

def get_database_url() -> str:
    """
    Resolves the MSSQL connection string from environment variables,
    .env file, or standard Healthcare Connect configuration.
    Avoids hardcoding paths.
    """
    try:
        from dotenv import load_dotenv
        load_dotenv(".env")
        load_dotenv("backend/.env")
    except Exception:
        pass

    # 0. Check explicit test database flag or database name
    db_name = os.getenv("DATABASE_NAME")
    if os.getenv("USE_TEST_DB") == "1" or os.getenv("USE_TEST_DATABASE") == "1":
        db_name = "HealthCare_connect_test"

    if db_name:
        return (
            "mssql+pyodbc:///?odbc_connect="
            "DRIVER%3D%7BODBC+Driver+17+for+SQL+Server%7D%3B"
            "SERVER%3D.%3B"
            f"DATABASE%3D{db_name}%3B"
            "Trusted_Connection%3Dyes%3B"
            "TrustServerCertificate%3Dyes%3B"
        )

    # 1. Direct environment variable
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return db_url

    # 2. Check local or shared .env
    try:
        from dotenv import dotenv_values
        # Current directory .env
        env_dict = dotenv_values(".env")
        if env_dict.get("DATABASE_URL"):
            return env_dict["DATABASE_URL"]
            
        # Parent directory or Healthcare Connect .env if available
        shared_env = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")
        if os.path.exists(shared_env):
            env_dict = dotenv_values(shared_env)
            if env_dict.get("DATABASE_URL"):
                return env_dict["DATABASE_URL"]
    except Exception:
        pass

    return DEFAULT_DATABASE_URL

_engine = None

def reset_engine():
    """Disposes and resets the cached SQLAlchemy engine."""
    global _engine
    if _engine is not None:
        try:
            _engine.dispose()
        except Exception:
            pass
        _engine = None

def get_engine():
    """
    Returns a shared, pooled SQLAlchemy engine instance.
    Configured with connection stability parameters matching Healthcare Connect.
    """
    global _engine
    if _engine is None and create_engine is not None:
        db_url = get_database_url()
        try:
            _engine = create_engine(
                db_url,
                echo=False,
                pool_pre_ping=True,      # Tests connection liveness
                pool_recycle=300,        # Recycles sockets to prevent stale connections
                pool_size=10,
                max_overflow=20
            )
            logger.info("Timeline MSSQL engine initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to create MSSQL engine: {e}")
            _engine = None
    return _engine

@contextmanager
def get_db_session() -> Generator[Optional[Session], None, None]:
    """
    Context manager yielding a transactional Session.
    Returns None if database engine is unavailable.
    """
    engine = get_engine()
    if engine is None or Session is None:
        yield None
        return

    session = Session(engine)
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def get_session() -> Generator[Optional[Session], None, None]:
    """
    FastAPI Depends(get_session) dependency generator matching Healthcare Connect.
    """
    engine = get_engine()
    if engine is None or Session is None:
        yield None
        return
    with Session(engine) as session:
        yield session

def test_connection() -> bool:
    """Verifies that the database is reachable and responsive."""
    try:
        with get_db_session() as session:
            if session is None or text is None:
                return False
            res = session.execute(text("SELECT 1")).scalar()
            return res == 1
    except Exception as e:
        logger.warning(f"Database connectivity test failed: {e}")
        return False
