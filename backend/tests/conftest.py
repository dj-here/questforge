import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Set testing environment variables
os.environ["TESTING"] = "True"
os.environ["SECRET_KEY"] = "test-secret-key-32-bytes-minimum-length-for-testing"
os.environ["DATABASE_URL"] = "sqlite:///./test_questforge.db"
os.environ["MOCK_LLM"] = "True"
os.environ["SANDBOX_TYPE"] = "mock"
os.environ["HACKERRANK_DRY_RUN"] = "True"

from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.seed.seed_data import seed_initial_data
from backend.app.auth import create_access_token
from backend.app.models import UserRole

# Test DB Engine
TEST_DATABASE_URL = "sqlite:///./test_questforge.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    seed_initial_data(db)
    db.close()
    yield
    Base.metadata.drop_all(bind=test_engine)
    if os.path.exists("./test_questforge.db"):
        try:
            os.remove("./test_questforge.db")
        except Exception:
            pass

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

@pytest.fixture
def admin_token():
    return create_access_token({"sub": "admin@questforge.io", "role": UserRole.ADMIN.value})

@pytest.fixture
def reviewer_token():
    return create_access_token({"sub": "reviewer@questforge.io", "role": UserRole.REVIEWER.value})

@pytest.fixture
def auth_headers(reviewer_token):
    return {"Authorization": f"Bearer {reviewer_token}"}

@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}
