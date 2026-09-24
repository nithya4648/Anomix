# 🌐 Anomix Production Deployment Guide

This guide covers deployment options for **Anomix** across local development, Docker Compose containerization, and cloud platforms like Railway or Render.

---

## 1. 🐳 Docker Compose Deployment (Recommended)

Production containerized deployment spins up the FastAPI backend, PostgreSQL database, Redis cache, Vite React frontend, and the automated Real Metrics Collector.

```bash
# Build and launch all services in detached mode
docker-compose up -d --build

# Inspect running containers
docker-compose ps

# Tail service logs
docker-compose logs -f
```

- **Frontend Application**: `http://localhost:80`
- **Backend REST API & Docs**: `http://localhost:8000/docs`
- **WebSocket Feed**: `ws://localhost:8000/ws/api/v1/updates`

---

## 2. ☁️ Railway Cloud Deployment

### Prerequisites
- [Railway CLI](https://docs.railway.app/cli/installation) installed or Railway Web Console account.
- GitHub repository connected to your Railway account.

### Step-by-Step Instructions
1. **Push Changes to GitHub**:
   ```bash
   git add .
   git commit -m "Upgrade Anomix UI and integrate real psutil system metrics"
   git push origin main
   ```

2. **Deploy on Railway**:
   - Go to [railway.app](https://railway.app) and create a **New Project**.
   - Select **Deploy from GitHub repo** and select `Anomix`.
   - Add a **PostgreSQL** database plugin to the project.
   - Set required Environment Variables:
     ```env
     DATABASE_URL=${POSTGRES_URL}
     REDIS_URL=${REDIS_URL}
    CORS_ORIGINS=["https://your-frontend-domain.up.railway.app"]
     ```
   - Railway automatically reads `Dockerfile.backend` and `Dockerfile.frontend` to instantiate services.

---

## 3. ⚙️ Render Cloud Deployment

1. Create a **Web Service** for the backend pointing to `Dockerfile.backend`.
2. Create a **Static Site** for the frontend pointing to `frontend/dist` with Build Command `npm run build`.
3. Set environment variable `VITE_WS_URL` to your backend websocket URL.
4. Set the backend `CORS_ORIGINS` environment variable to a JSON array containing
  the exact frontend origin, with no trailing slash:
  ```env
  CORS_ORIGINS=["https://anomix-omega.vercel.app"]
  ```

---

## 🔧 Troubleshooting & Diagnostics

- **WebSocket Fails to Connect**:
  Verify CORS settings in `.env`. Ensure `CORS_ORIGINS` includes your frontend origin.
- **Psutil Metric Collection Error**:
  Ensure Python has permission to access system counters or run `python scripts/real_metrics_integration.py demo` to test isolation.
