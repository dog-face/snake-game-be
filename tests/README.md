# Test Suite

This directory contains the pytest test suite for the Snake Game backend API.

## Running Tests

**IMPORTANT: You must activate the virtual environment first!**

### Option 1: Activate venv manually
```bash
# From the project root directory
source venv/bin/activate
pytest
```

### Option 2: Use the test script (recommended)
```bash
# From the project root directory
./run_tests.sh
```

### Option 3: One-liner
```bash
source venv/bin/activate && pytest
```

### Run all tests:
```bash
source venv/bin/activate
pytest
```

### Run with verbose output:
```bash
source venv/bin/activate
pytest -v
```

### Run specific test file:
```bash
pytest tests/test_auth.py
```

### Run specific test class:
```bash
pytest tests/test_auth.py::TestSignup
```

### Run specific test:
```bash
pytest tests/test_auth.py::TestSignup::test_signup_success
```

### Run with coverage:
```bash
pytest --cov=app --cov-report=html
```

## Test Structure

- `test_auth.py` - Authentication endpoint tests (signup, login, logout, get me)
- `test_leaderboard.py` - Leaderboard endpoint tests (get, submit)
- `test_watch.py` - Watch endpoint tests (active players, start, update, end)
- `test_security.py` - Security tests (password hashing, JWT tokens)
- `test_schemas.py` - Schema validation tests

## Test Fixtures

- `test_db` - In-memory SQLite database session for each test
- `client` - Async HTTP client for making API requests
- `test_user` - Pre-created test user
- `test_user_token` - JWT token for test user
- `authenticated_client` - HTTP client with authentication headers

## Notes

- Tests use an in-memory SQLite database that is created and destroyed for each test
- All database operations are async
- Tests are isolated - each test gets a fresh database

