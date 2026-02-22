import os

import pytest

# Set test env vars before importing app code
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://reconforge:devpassword@localhost:5432/reconforge_test")
os.environ.setdefault("ENVIRONMENT", "testing")


@pytest.fixture
def anyio_backend():
    return "asyncio"
