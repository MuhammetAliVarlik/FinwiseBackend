# app/repositories/user_repository.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base_repository import BaseRepository
from app.models.user import User

class UserRepository(BaseRepository):
    def __init__(self, db: AsyncSession):
        super().__init__(db, User)

    async def get_by_email(self, email: str) -> User | None:
        # NEW: Construct the query using 'select'
        query = select(User).where(User.email == email)
        
        # NEW: Await the execution
        result = await self.db.execute(query)
        
        # NEW: Return the scalar (the actual User object)
        return result.scalars().first()