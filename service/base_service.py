from sqlalchemy.orm import Session
from database import SessionLocal


class BaseService:

    def __init__(self):
        self.db: Session = SessionLocal()

    def close(self):
        self.db.close()
