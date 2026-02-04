# Testing Guide for LDAPGuard

## Overview

This project includes a comprehensive test suite using **pytest** to ensure code quality, reliability, and maintainability.

## Test Structure

```
tests/
├── __init__.py                      # Test package initialization
├── conftest.py                      # Pytest fixtures and configuration
├── test_core_security.py            # Security utilities tests
├── test_core_encryption.py          # Encryption utilities tests
├── test_routes_auth.py              # Authentication routes tests
├── test_routes_ldap_servers.py      # LDAP server management tests
├── test_routes_backups.py           # Backup management tests
├── test_routes_restores.py          # Restore operation tests
├── test_schemas.py                  # Pydantic schema validation tests
├── test_services_backup.py          # Backup service tests
└── test_services_ldap.py            # LDAP service tests
```

## Running Tests

### Install Test Dependencies

```bash
pip install -r requirements.txt
```

### Run All Tests

```bash
pytest
```

### Run Tests with Coverage Report

```bash
pytest --cov=api --cov-report=html
```

This generates an HTML coverage report in `htmlcov/index.html`

### Run Specific Test File

```bash
pytest tests/test_core_security.py
```

### Run Specific Test

```bash
pytest tests/test_core_security.py::TestPasswordHashing::test_get_password_hash
```

### Run Tests with Verbose Output

```bash
pytest -v
```

### Run Only Unit Tests

```bash
pytest -m unit
```

### Run Only Integration Tests

```bash
pytest -m integration
```

### Run Tests in Watch Mode (requires pytest-watch)

```bash
pip install pytest-watch
ptw
```

## Test Coverage Goals

- **Minimum Coverage**: 80% of code
- **Critical Paths**: 100% coverage (security, authentication, encryption)
- **Routes**: 90% coverage
- **Services**: 85% coverage

## Writing New Tests

### Test File Naming Convention

- Test files: `test_*.py`
- Test classes: `Test*` (e.g., `TestPasswordHashing`)
- Test methods: `test_*` (e.g., `test_get_password_hash`)

### Test Template

```python
"""Tests for [module name]."""
import pytest
from [module] import [function]


class TestFeatureName:
    """Test [feature] functionality."""

    def test_successful_operation(self):
        """Test that operation succeeds."""
        # Arrange
        data = {...}
        
        # Act
        result = function(data)
        
        # Assert
        assert result == expected

    def test_error_handling(self):
        """Test that errors are handled."""
        with pytest.raises(ExceptionType):
            function(invalid_data)
```

### Using Fixtures

Fixtures are defined in `conftest.py` and can be used in any test:

```python
def test_with_client(client):
    """Test using the test client fixture."""
    response = client.get("/")
    assert response.status_code == 200

def test_with_db(db):
    """Test using the database fixture."""
    # db is a SQLAlchemy session
    pass

def test_with_user_data(test_user_data):
    """Test using test user data fixture."""
    assert test_user_data["username"] == "testuser"
```

### Testing Async Functions

```python
@pytest.mark.asyncio
async def test_async_function(self):
    """Test an async function."""
    result = await async_function()
    assert result == expected
```

## Available Fixtures

- **client**: TestClient for making HTTP requests
- **db**: Test database session (SQLite in-memory)
- **mock_redis**: Mock Redis client
- **mock_ldap**: Mock LDAP connection
- **test_user_data**: Sample user data for tests
- **test_ldap_server_data**: Sample LDAP server configuration

## Best Practices

1. **Isolation**: Each test should be independent
2. **Clarity**: Test names should describe what they test
3. **Arrange-Act-Assert**: Follow the AAA pattern
4. **Mocking**: Mock external dependencies (LDAP, Redis)
5. **Fixtures**: Use fixtures for common setup
6. **Parametrize**: Use `@pytest.mark.parametrize` for multiple scenarios

### Example with Parametrization

```python
@pytest.mark.parametrize("input,expected", [
    ("password", True),
    ("", False),
    (None, False)
])
def test_validate_password(input, expected):
    """Test password validation with multiple inputs."""
    assert validate(input) == expected
```

## Continuous Integration

Tests run automatically on:
- Every commit (pre-commit hooks)
- Pull requests (CI/CD pipeline)
- Scheduled nightly builds

## Troubleshooting

### Import Errors

If you get import errors, ensure:
```bash
export PYTHONPATH=/path/to/LDAPGuard:$PYTHONPATH
```

### Database Errors

The test database (SQLite) is created in-memory. If you need to debug:
```python
# In conftest.py, change to:
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_debug.db"
```

### Async Errors

Ensure `pytest-asyncio` is installed:
```bash
pip install pytest-asyncio
```

## Contributing Tests

When adding new features:
1. Write tests first (TDD approach recommended)
2. Ensure tests pass: `pytest`
3. Check coverage: `pytest --cov=api`
4. Keep coverage above 80%

## Performance Testing

For performance-critical tests:

```python
import pytest

@pytest.mark.slow
def test_large_backup_processing(self):
    """Test processing large backup files."""
    # This test may take longer
    pass
```

Run only fast tests:
```bash
pytest -m "not slow"
```

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/advanced/testing-dependencies/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/20/faq/testing.html)
