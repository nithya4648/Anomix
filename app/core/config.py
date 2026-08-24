from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str
    database_pool_size: int = 20
    database_max_overflow: int = 10

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    debug: bool = False

    # Security
    secret_key: str
    api_key_header: str = "X-API-Key"
    api_key: str

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    cors_allow_headers: list[str] = ["Content-Type", "Authorization", "X-API-Key"]

    # ML
    anomaly_detection_method: str = "isolation_forest"  # or z_score
    z_score_threshold: float = 3.0
    isolation_forest_contamination: float = 0.1
    min_samples_for_detection: int = 50
    eval_threshold_confidence: float = 0.5

    # Monitoring
    log_level: str = "INFO"
    metrics_retention_days: int = 30
    anomaly_aggregation_window_minutes: int = 5

    # Redis
    redis_url: str = "redis://redis:6379/0"
    use_redis: bool = False

    # WebSocket
    ws_heartbeat_interval: int = 30
    ws_max_connections: int = 1000

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
