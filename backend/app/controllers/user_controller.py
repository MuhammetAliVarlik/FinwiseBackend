# app/controllers/user_controller.py
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.controllers.base_controller import BaseController
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService
from app.schemas.user import UserCreate, UserOut
from app.core.database import SessionLocal


def get_user_service():
    """Global dependency that can be safely used by FastAPI."""
    db: Session = SessionLocal()
    try:
        repo = UserRepository(db)
        service = UserService(repo)
        yield service
    finally:
        db.close()


class UserController(BaseController):
    def __init__(self):
        super().__init__(prefix="/users", tags=["Users"])
        self.router.add_api_route(
            "/", self.create_user, methods=["POST"], response_model=UserOut
        )
        self.router.add_api_route(
            "/", self.list_users, methods=["GET"], response_model=List[UserOut]
        )

    def create_user(self, user: UserCreate, service: UserService = Depends(get_user_service)) -> UserOut:
        try:
            return service.register_user(user.name, user.email)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    def list_users(self, service: UserService = Depends(get_user_service)) -> List[UserOut]:
        return service.get_all()
