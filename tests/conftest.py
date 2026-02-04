"""Pytest configuration and fixtures."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import create_engine
from api.main import app
from api.core.database import Base, get_db
from api.models import models  # noqa: F401
from unittest.mock import patch

# Use SQLite database for async tests
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
sync_engine = create_engine(
    "sqlite:///./test.db", connect_args={"check_same_thread": False}
)
TestingSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def override_get_db():
    """Override database dependency for testing."""
    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create test database tables."""
    Base.metadata.create_all(bind=sync_engine)
    yield
    Base.metadata.drop_all(bind=sync_engine)


@pytest.fixture
def client():
    """Create test client."""
    Base.metadata.create_all(bind=sync_engine)
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=sync_engine)


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    with patch('redis.Redis') as mock:
        yield mock


@pytest.fixture
def mock_ldap():
    """Create a mock LDAP connection."""
    with patch('ldap.initialize') as mock:
        yield mock


@pytest.fixture
def test_user_data():
    """Provide test user data."""
    return {
        "username": "testuser",
        "password": "TestPassword123!",
        "email": "test@example.com"
    }


@pytest.fixture
def test_ldap_server_data():
    """Provide test LDAP server configuration."""
    return {
        "name": "Test LDAP Server",
        "host": "ldap.example.com",
        "port": 389,
        "use_ssl": False,
        "base_dn": "dc=example,dc=com",
        "bind_dn": "cn=admin,dc=example,dc=com",
        "bind_password": "password123"
    }
