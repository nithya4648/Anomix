from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.core.database import init_db
from app.api import metrics, incidents, ml, websocket, alerts, analytics, config


logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    import asyncio
    from app.services.stream_consumer import start_stream_consumer

    # Startup
    logger.info("PulseWatch API starting...")
    init_db()
    logger.info("Database initialized")

    consumer_task = None

    if settings.use_redis:
        consumer_task = asyncio.create_task(start_stream_consumer())
        logger.info("Started Redis Streams background consumer task.")

    yield

    # Shutdown
    logger.info("PulseWatch API shutting down...")

    if consumer_task:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""

    configure_logging()

    app = FastAPI(
        title="PulseWatch API",
        description="Real-time anomaly detection platform",
        version="0.1.0",
        lifespan=lifespan,
    )

    from slowapi.middleware import SlowAPIMiddleware
    from slowapi.errors import RateLimitExceeded
    from fastapi.responses import JSONResponse
    from app.core.limiter import limiter

    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        return JSONResponse(
            status_code=429,
            content={"detail": f"Rate limit exceeded: {exc.detail}"},
        )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        logger.debug(f"{request.method} {request.url.path}")

        response = await call_next(request)

        logger.debug(
            f"{request.method} {request.url.path} -> {response.status_code}"
        )

        return response

    # Include routers
    app.include_router(metrics.router)
    app.include_router(incidents.router)
    app.include_router(ml.router)
    app.include_router(websocket.router)
    app.include_router(config.router)
    app.include_router(alerts.router)
    app.include_router(analytics.router)

    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        from app.core.database import SessionLocal
        from sqlalchemy import text
        from fastapi import HTTPException
        import redis.asyncio as aioredis
        
        db_ok = True
        redis_ok = True
        try:
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            db.close()
        except Exception:
            db_ok = False
        
        if settings.use_redis:
            try:
                r = aioredis.from_url(settings.redis_url)
                await r.ping()
                await r.close()
            except Exception:
                redis_ok = False
                
        status_val = "ok" if db_ok and redis_ok else "error"
        if status_val == "error":
            raise HTTPException(status_code=503, detail={"status": "error", "db_ok": db_ok, "redis_ok": redis_ok})
            
        return {
            "status": status_val,
            "service": "pulsewatch",
            "version": "0.1.0",
            "db_ok": db_ok,
            "redis_ok": redis_ok
        }

    @app.get("/api/v1/info")
    async def api_info():
        """API information endpoint"""
        return {
            "name": "PulseWatch",
            "version": "0.1.0",
            "description": "Real-time anomaly detection platform",
            "anomaly_detection_method": settings.anomaly_detection_method,
            "min_samples_required": settings.min_samples_for_detection,
        }

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        workers=settings.api_workers,
    )
