# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

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

    # CORS - Accept from Nginx proxy and direct connections
    cors_origins: list[str] = [
        "http://localhost",
        "http://localhost:80",
        "http://127.0.0.1",
        "http://127.0.0.1:80",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://anomix-omega.vercel.app",
    ]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = [
        "GET",
        "POST",
        "PUT",
        "DELETE",
        "OPTIONS",
        "PATCH",
    ]
    cors_allow_headers: list[str] = [
        "Content-Type",
        "Authorization",
        "X-API-Key",
        "Accept",
        "Origin",
    ]

    # ML / Anomaly Detection
    anomaly_detection_method: str = "isolation_forest"
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



@lru_cache()
def get_settings() -> Settings:
    return Settings()
