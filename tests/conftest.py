"""Pytest configuration and fixtures."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from api.main import app
from api.core.database import Base, get_db
import os
from unittest.mock import Mock, patch

# Use in-memory SQLite database for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create test database tables."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    """Get test database session."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    yield TestingSessionLocal()
    # Clean up
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db):
    """Create test client."""
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


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
