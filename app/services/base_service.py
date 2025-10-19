class BaseService:
    def __init__(self, repository):
        self.repo = repository

    def get_all(self):
        return self.repo.get_all()

    def create(self, data: dict):
        return self.repo.create(data)
