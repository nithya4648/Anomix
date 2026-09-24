import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.utils.auth import create_access_token
from unittest.mock import patch
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import init_db

@pytest.fixture
def client():
    init_db()
    with TestClient(app) as c:
        yield c

@pytest.fixture
def auth_headers():
    token = create_access_token(data={"sub": "testuser"})
    return {"Authorization": f"Bearer {token}"}

def test_mocked_db_failure_503(client, auth_headers):
    with patch("app.services.metrics.metric_service.MetricService.ingest_metric") as mock_ingest:

        mock_ingest.side_effect = SQLAlchemyError("DB connection lost")
        res = client.post(
            "/api/v1/metrics/ingest", 
            json={"metric_name": "err_test", "value": 1.0}, 
            headers=auth_headers
        )
        assert res.status_code == 503

def test_empty_metric_name_422(client, auth_headers):
    res = client.post(
        "/api/v1/metrics/ingest", 
        json={"metric_name": "", "value": 1.0}, 
        headers=auth_headers
    )
    assert res.status_code == 422

def test_mocked_redis_connection_error_succeeds(client, auth_headers, caplog):
    with patch("app.api.metrics.aioredis.from_url") as mock_redis:
        mock_redis.side_effect = Exception("Connection refused")
        with patch("app.core.config.get_settings") as mock_settings:
            class MockSettings:
                use_redis = True
                redis_url = "redis://fake:6379"
                anomaly_detection_method = "isolation_forest"
                z_score_threshold = 3.0
                isolation_forest_contamination = 0.1
                min_samples_for_detection = 50
            mock_settings.return_value = MockSettings()
            
            res = client.post(
                "/api/v1/metrics/ingest", 
                json={"metric_name": "redis_err_test", "value": 1.0}, 
                headers=auth_headers
            )
            assert res.status_code == 200


