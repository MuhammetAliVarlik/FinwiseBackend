import pytest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import Base

from app.models.user import User
from app.models.stock import Stock

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    pool_pre_ping=True
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function", autouse=True)
def override_db(monkeypatch):

    print(f"\n[DEBUG] Kayıtlı Tablolar: {Base.metadata.tables.keys()}")

    Base.metadata.create_all(bind=engine)
    
    monkeypatch.setattr("app.core.database.SessionLocal", TestingSessionLocal)
    
    monkeypatch.setattr("app.controllers.user_controller.SessionLocal", TestingSessionLocal)
    monkeypatch.setattr("app.controllers.stock_controller.SessionLocal", TestingSessionLocal)
    
    yield
    
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client():
    with TestClient(app) as c:
        yield c