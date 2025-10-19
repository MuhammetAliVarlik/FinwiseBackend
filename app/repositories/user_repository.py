from repositories.base_repository import BaseRepository
from models.user import User

class UserRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, User)

    def get_by_email(self, email: str):
        return self.db.query(User).filter(User.email == email).first()
