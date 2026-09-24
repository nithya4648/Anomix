import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db, Base

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.models.anomaly import Anomaly
from datetime import datetime, timezone
from app.schemas import AnomalyFeedbackRequest

from app.utils.auth import create_access_token

# Use a separate test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_anomaly_feedback.db"
TestEngine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TestEngine)

# Override dependency
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(autouse=True)
def create_test_db():
    app.dependency_overrides[get_db] = override_get_db
    # Create tables
    Base.metadata.create_all(bind=TestEngine)
    yield
    Base.metadata.drop_all(bind=TestEngine)
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client

@pytest.fixture
def auth_headers():
    token = create_access_token(data={"sub": "testuser"})
    return {"Authorization": f"Bearer {token}"}

def test_add_anomaly_feedback_success(client, auth_headers):
    # Insert a sample anomaly directly via DB
    db = next(override_get_db())
    anomaly = Anomaly(
        metric_name="test_metric",
        metric_id="metric123",
        anomaly_timestamp=datetime(2023, 1, 1, tzinfo=timezone.utc),
        value=123.4,
        confidence_score=0.95,
        detection_method="test",
        is_confirmed=False,
    )
    db.add(anomaly)
    db.commit()
    db.refresh(anomaly)

    payload = {
        "feedback_status": "true_positive",
        "feedback_note": "Looks correct",
    }
    response = client.post(f"/api/v1/anomalies/{anomaly.id}/feedback", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["feedback_status"] == "true_positive"
    assert data["feedback_note"] == "Looks correct"
    assert data["feedback_at"] is not None

def test_add_anomaly_feedback_not_found(client, auth_headers):
    payload = {"feedback_status": "false_positive", "feedback_note": "Incorrect"}
    response = client.post("/api/v1/anomalies/nonexistent-id/feedback", json=payload, headers=auth_headers)
    assert response.status_code == 404

