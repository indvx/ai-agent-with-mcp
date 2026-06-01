from sqlalchemy.orm import Session
from sql.crud import users as user_crud
from service.base_service import BaseService


class UserService(BaseService):
    def __init__(self):
        super().__init__()

    def get_user(self, user_id: int):
        return user_crud.get_user_by_id(self.db, user_id)
