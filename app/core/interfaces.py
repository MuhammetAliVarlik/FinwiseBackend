# app/core/interfaces.py
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional

ModelType = TypeVar("ModelType") 
class IRepository(ABC, Generic[ModelType]):
    """
    Generic repository interface for basic CRUD operations.
    """

    @abstractmethod
    def get_all(self) -> List[ModelType]:
        """Retrieve all records from the repository."""
        pass

    @abstractmethod
    def get_by_id(self, record_id: int) -> Optional[ModelType]:
        """Retrieve a single record by its unique identifier."""
        pass

    @abstractmethod
    def create(self, model_instance: ModelType) -> ModelType:
        """Persist a new model instance into the database."""
        pass


class IService(ABC, Generic[ModelType]):
    """
    Generic service interface for business logic layer.
    """

    @abstractmethod
    def get_all(self) -> List[ModelType]:
        """Fetch all records via repository layer."""
        pass

    @abstractmethod
    def create(self, model_data: dict) -> ModelType:
        """Validate and create a new model record."""
        pass


class IController(ABC):
    """
    Interface for API controllers.
    """

    @abstractmethod
    def register_routes(self) -> None:
        """Define and register API routes with the FastAPI router."""
        pass
