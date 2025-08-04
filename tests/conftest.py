"""
Pytest configuration and fixtures
"""

import pytest
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
import os

from app.main import app
from app.core.database import Base
from app.core.dependencies import get_db
from app.models.user import User
from app.core.auth import get_password_hash


# Test database URL - use a separate test database
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://synapse_user:synapse_pass@localhost:5432/synapse_test"
)

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
    echo=False
)

# Create test session factory
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest.fixture(scope="session")
def anyio_backend():
    """Use asyncio backend for async tests"""
    return "asyncio"


@pytest.fixture(scope="function")
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Create test database session"""
    async with test_engine.begin() as conn:
        # Create tables
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()
    
    async with test_engine.begin() as conn:
        # Drop tables after test
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db():
    """Override dependency for testing"""
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture(scope="function")
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with overridden dependencies"""
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


async def create_test_user(
    db: AsyncSession,
    email: str = "test@example.com",
    password: str = "testpass123",
    role: str = "Tester"
) -> User:
    """Helper to create test user"""
    user = User(
        email=email,
        username=email,
        full_name="Test User",
        hashed_password=get_password_hash(password),
        role=role,
        is_active=True,
        is_superuser=False,
        lob_id=1
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def test_user(db: AsyncSession) -> User:
    """Create a test user"""
    return await create_test_user(db)


@pytest.fixture
async def auth_headers(test_user: User) -> dict:
    """Create auth headers for test user"""
    # In a real implementation, you would generate a proper JWT token
    # For testing, we'll use a mock token
    return {"Authorization": f"Bearer test-token-{test_user.user_id}"}


# Mock authentication for testing
async def mock_get_current_user():
    """Mock current user for testing"""
    return User(
        user_id=1,
        email="test@example.com",
        username="test@example.com",
        role="Tester",
        is_active=True
    )