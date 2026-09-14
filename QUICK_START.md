# 🚀 Anomix Platform Quick Start Guide (15-Minute Setup)

Welcome to **Anomix**, an AI-powered real-time anomaly detection and monitoring platform for system metrics.

---

## ⚡ Prerequisites

- **Python**: 3.11+
- **Node.js**: v18+ & npm
- **Git**

---

## 🛠️ Quick Local Setup

### Step 1: Start Backend API Service (Terminal 1)

```bash
# Navigate to project root
cd Anomix

# Install Python dependencies
pip install -e .
pip install psutil httpx

# Launch FastAPI backend with uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
> *Expected output: `Application startup complete. Uvicorn running on http://0.0.0.0:8000`*

---

### Step 2: Launch Modern React Frontend (Terminal 2)

```bash
cd frontend

# Install UI packages
npm install

# Start Vite Development Server
npm run dev
```
> *Expected output: `VITE vX.X.X ready in XXX ms. Local: http://localhost:5173/`*

---

### Step 3: Run Real System Metrics Collector (Terminal 3)

```bash
# Continuous real OS metrics telemetry collection
python scripts/real_metrics_integration.py
```
> *Expected output: `[INFO] Starting Anomix Real Metrics Collector continuously (Interval: 10.0s)...`*

---

## 🖥️ Accessing the Platform

Open your browser to: **`http://localhost:5173`**

### What to expect on the dashboard:
1. **Modern Dark UI**: Vibrant glassmorphic gradient cards for CPU, Memory, Anomalies, and Incidents.
2. **Real-time Live Telemetry**: Metrics sampled directly from your OS kernel via `psutil`.
3. **Connection Indicator**: Green **"WebSocket Live"** badge demonstrating streaming status.
4. **Auto-refresh Controls**: Toggle auto-refresh with manual sync buttons.
6. **Interactive Anomaly Feedback**: Click the **Feedback** action on any anomaly row to classify (True Positive / False Alarm) and attach investigation notes.
7. **Automated Recovery**: Incidents automatically transition to **Resolved** when metrics remain normal through the configurable `RECOVERY_CONFIRMATION_MINUTES` window.

