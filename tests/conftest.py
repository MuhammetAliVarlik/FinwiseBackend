# app/tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.database import Base, get_db
import os
import time
from sqlalchemy.exc import OperationalError

TEST_DATABASE_URL = os.getenv("DATABASE_URL")

# Wait until the test database is ready
for attempt in range(30):
    try:
        test_engine = create_engine(TEST_DATABASE_URL)
        connection = test_engine.connect()
        connection.close()
        break
    except OperationalError:
        print("Waiting for test DB...")
        time.sleep(1)
else:
    raise Exception("Test DB did not become ready in time")

TestingSessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=test_engine
)

# Dependency override for FastAPI
def override_get_db_session():
    db_session = TestingSessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()

app.dependency_overrides[get_db] = override_get_db_session

@pytest.fixture(scope="session")
def client():
    # Create all tables for the test DB
    Base.metadata.create_all(bind=test_engine)
    with TestClient(app) as client_instance:
        yield client_instance
