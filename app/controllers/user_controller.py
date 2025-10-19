# app/controllers/user_controller.py
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from controllers.base_controller import BaseController
from repositories.user_repository import UserRepository
from services.user_service import UserService
from schemas.user import UserCreate, UserOut
from core.database import SessionLocal

class UserController(BaseController):
    def __init__(self):
        super().__init__(prefix="/users", tags=["Users"])
        # Lambda ile self bağlaması yapıldı
        self.router.post("/", response_model=UserOut)(
            lambda user, service=Depends(self._get_service): self.create_user(user, service)
        )
        self.router.get("/", response_model=List[UserOut])(
            lambda service=Depends(self._get_service): self.list_users(service)
        )

    def _get_service(self) -> UserService:
        db: Session = SessionLocal()
        try:
            repo = UserRepository(db)
            service = UserService(repo)
            yield service
        finally:
            db.close()

    def create_user(self, user: UserCreate, service: UserService):
        try:
            return service.register_user(user.name, user.email)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    def list_users(self, service: UserService):
        return service.get_all()
