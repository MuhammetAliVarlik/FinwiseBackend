# app/services/user_service.py
from app.services.base_service import BaseService
from app.models.user import User

class UserService(BaseService):
    async def register_user(self, name: str, email: str):
        # NEW: Await the check
        existing_user = await self.repo.get_by_email(email)
        if existing_user:
            raise ValueError("Email already registered")
        
        user = User(name=name, email=email)
        
        # NEW: Await the creation
        return await self.repo.create(user)