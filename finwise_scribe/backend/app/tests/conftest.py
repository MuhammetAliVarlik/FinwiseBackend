# app/tests/conftest.py
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db

# Use aiosqlite for async in-memory testing
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Global Test Engine
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autocommit=False, 
    autoflush=False
)

# --- FIXED: Changed scope from 'session' to 'function' to match event loop ---
@pytest_asyncio.fixture(scope="function", autouse=True)
async def close_db_engine():
    """
    Ensures the database engine is disposed of after EVERY test.
    This prevents the CI runner from hanging due to open connections.
    """
    yield
    await engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def async_db():
    """
    Creates tables before each test and drops them after.
    Yields an async session.
    """
    # 1. Create Tables (Async)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 2. Create Session
    async with TestingSessionLocal() as session:
        yield session
    
    # 3. Drop Tables (Cleanup)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(scope="function")
async def client(async_db):
    """
    Overrides the get_db dependency to use the test session,
    and returns an AsyncClient for requests.
    """
    # Override the dependency
    async def override_get_db():
        yield async_db

    app.dependency_overrides[get_db] = override_get_db
    
    # Use ASGITransport for newer httpx versions
    transport = ASGITransport(app=app)
    
    # Return AsyncClient with the transport
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    
    # Clear override after test
    app.dependency_overrides.clear()