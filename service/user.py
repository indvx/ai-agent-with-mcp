from sqlalchemy.orm import Session
from sql.crud import users as user_crud


class UserService:
    def __init__(self, db: Session = None):
        self.db = db

    def __db_close(self):
        self.db.close()

    def get_user(self, user_id: int):
        user = user_crud.get_user_by_id(self.db, user_id)
        if not user:
            raise Exception("User not found")
        return user

    def delete_user(self, user_id: int):
        user = self.get_user(user_id)
        user_crud.delete_user(self.db, user.id)
        return {"message": "User deleted"}

    def get_users(self, page: int = 1, limit: int = 20):
        return user_crud.get_users(self.db, page=page, limit=limit)
