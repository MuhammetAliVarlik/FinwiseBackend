# app/services/user_service.py
from app.services.base_service import BaseService
from app.models.user import User

class UserService(BaseService):
    def register_user(self, name: str, email: str):
        if self.repo.get_by_email(email):
            raise ValueError("Email already registered")
        user = User(name=name, email=email)
        return self.repo.create(user)
