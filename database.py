from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from dotenv import load_dotenv
import os

load_dotenv()

# Build the database connection string from environment variables
SQLALCHEMY_DATABASE_URL = "{}://{}:{}@{}:{}/{}".format(
    os.getenv("DB_CONNECTION", default="mysql+pymysql"),
    os.getenv("MYSQL_USER", default="root"),
    os.getenv("MYSQL_PASSWORD", default="root"),
    os.getenv("MYSQL_HOST", default="localhost"),
    os.getenv("MYSQL_PORT", default="3306"),
    os.getenv("MYSQL_DATABASE", default="python"),
)

# pool_pre_ping automatically reconnects if MySQL drops stale connections
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=5,
    pool_pre_ping=True,
    isolation_level="READ COMMITTED",
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
