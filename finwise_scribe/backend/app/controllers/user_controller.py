# app/controllers/user_controller.py
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.controllers.base_controller import BaseController
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService
from app.schemas.user import UserCreate, UserOut
from app.core.database import get_db

# NEW: Async Dependency Injection
async def get_user_service(db: AsyncSession = Depends(get_db)):
    """
    Injects the AsyncSession into the Repo, and the Repo into the Service.
    FastAPI handles the 'await' for the dependency.
    """
    repo = UserRepository(db)
    service = UserService(repo)
    return service

class UserController(BaseController):
    def __init__(self):
        super().__init__(prefix="/users", tags=["Users"])
        self.router.add_api_route(
            "/", self.create_user, methods=["POST"], response_model=UserOut
        )
        self.router.add_api_route(
            "/", self.list_users, methods=["GET"], response_model=List[UserOut]
        )

    # NEW: async def
    async def create_user(self, user: UserCreate, service: UserService = Depends(get_user_service)) -> UserOut:
        try:
            # NEW: await
            return await service.register_user(user.name, user.email)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    # NEW: async def
    async def list_users(self, service: UserService = Depends(get_user_service)) -> List[UserOut]:
        # NEW: await
        return await service.get_all()