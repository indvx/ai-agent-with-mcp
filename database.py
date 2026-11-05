from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
import os
from core.config import settings

# Build the database connection string from environment variables
SQLALCHEMY_DATABASE_URL = "{}://{}:{}@{}:{}/{}".format(
    settings.db_connection,
    settings.db_user,
    settings.db_password,
    settings.db_host,
    settings.db_port,
    settings.db_database,
)
connect_args = {}
if settings.db_ssl_mode == 'enable':
    with open("ca.pem", "w") as f:
        f.write(ca_cert_content)
    
    connect_args["ssl"] = {
        "ca": "ca.pem"
    }

# pool_pre_ping automatically reconnects if MySQL drops stale connections
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=5,
    pool_pre_ping=True,
    isolation_level="READ COMMITTED",
    connect_args=connect_args
)

# Factory for creating new database sessions per request
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# SessionLocal = scoped_session(SessionLocal)
Base = declarative_base()


# FastAPI dependency that provides a clean DB session per request and closes it after
def get_db():
    """Yields a database session and guarantees closure upon request completion."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
