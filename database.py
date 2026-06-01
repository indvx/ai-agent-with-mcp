from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from dotenv import load_dotenv
import os

load_dotenv()

SQLALCHEMY_DATABASE_URL = "{}://{}:{}@{}:{}/{}".format(
    os.getenv("DB_CONNECTION", default="mysql+pymysql"),
    os.getenv("MYSQL_USER", default="root"),
    os.getenv("MYSQL_PASSWORD", default="root"),
    os.getenv("MYSQL_HOST", default="localhost"),
    os.getenv("MYSQL_PORT", default="3306"),
    os.getenv("MYSQL_DATABASE", default="python"),
)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=5,
    pool_pre_ping=True,
    isolation_level="READ COMMITTED",
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# SessionLocal = scoped_session(SessionLocal)
Base = declarative_base()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
