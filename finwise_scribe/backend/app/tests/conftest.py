import pytest
import sys
import os

# Ensure backend directory is in python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool  # <--- CRITICAL IMPORT
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import Base

# Import models so they are registered in Base.metadata
from app.models.user import User
from app.models.stock import Stock

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # <--- KEEPS DB ALIVE IN MEMORY
    pool_pre_ping=True
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function", autouse=True)
def override_db(monkeypatch):
    """
    Creates tables before each test and drops them after.
    Monkeys patches SessionLocal to use the test database.
    """
    print(f"\n[DEBUG] Creating Tables: {Base.metadata.tables.keys()}")

    # Create tables in the static in-memory database
    Base.metadata.create_all(bind=engine)
    
    # Patch the dependency injection points
    monkeypatch.setattr("app.core.database.SessionLocal", TestingSessionLocal)
    monkeypatch.setattr("app.controllers.user_controller.SessionLocal", TestingSessionLocal)
    monkeypatch.setattr("app.controllers.stock_controller.SessionLocal", TestingSessionLocal)
    
    yield
    
    # Clean up after test
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client():
    with TestClient(app) as c:
        yield c