from core.interfaces import IRepository

class BaseRepository:
    def __init__(self, db, model):
        self.db = db
        self.model = model

    def get_all(self):
        return self.db.query(self.model).all()

    def get_by_id(self, id: int):
        return self.db.query(self.model).filter(self.model.id == id).first()

    def create(self, entity):
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

