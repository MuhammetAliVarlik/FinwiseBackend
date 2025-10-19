from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List

T = TypeVar("T")

class IRepository(ABC, Generic[T]):
    @abstractmethod
    def get_all(self) -> List[T]: ...
    @abstractmethod
    def get_by_id(self, id: int) -> T | None: ...
    @abstractmethod
    def create(self, entity: T) -> T: ...

class IService(ABC, Generic[T]):
    @abstractmethod
    def get_all(self) -> List[T]: ...
    @abstractmethod
    def create(self, data: dict) -> T: ...

class IController(ABC):
    @abstractmethod
    def register_routes(self):
        pass
