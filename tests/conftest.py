import pytest
from app.core.database import init_db

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Ensure database schema is created before tests run"""
    init_db()
