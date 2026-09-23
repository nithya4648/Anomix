import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.utils.auth import create_access_token
from app.core.limiter import limiter

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture
def auth_headers():
    token = create_access_token(data={"sub": "testuser"})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(autouse=True)
def reset_limiter():
    limiter.reset()

def test_ingest_appears_in_list(client, auth_headers):
    # Ingest a metric
    res = client.post(
        "/api/v1/metrics/ingest", 
        json={"metric_name": "int_test", "value": 42.0}, 
        headers=auth_headers
    )
    assert res.status_code == 200

    # Check that it appears in the recent list
    res2 = client.get("/api/v1/metrics/recent?metric_name=int_test", headers=auth_headers)
    assert res2.status_code == 200
    data = res2.json()
    assert len(data) > 0
    assert data[0]["value"] == 42.0

def test_rate_limit_1001st_request(client, auth_headers):
    # Use a specific IP for this test
    headers = auth_headers.copy()
    headers["X-Forwarded-For"] = "192.168.1.100"
    
    # Send 1000 requests, they should succeed
    for _ in range(1000):
        res = client.post(
            "/api/v1/metrics/ingest", 
            json={"metric_name": "rate_limit_test", "value": 1.0}, 
            headers=headers
        )
        assert res.status_code == 200

    # The 1001st request should be rate limited
    res = client.post(
        "/api/v1/metrics/ingest", 
        json={"metric_name": "rate_limit_test", "value": 1.0}, 
        headers=headers
    )
    assert res.status_code == 429

def test_out_of_bounds_value(client, auth_headers):
    res = client.post(
        "/api/v1/metrics/ingest", 
        json={"metric_name": "bounds_test", "value": 1e20}, 
        headers=auth_headers
    )
    assert res.status_code == 422
