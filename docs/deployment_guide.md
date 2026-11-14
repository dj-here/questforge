# QuestForge Deployment & Operations Guide

This guide covers deploying QuestForge locally via Docker Compose and across production cloud environments (VPS, AWS, Render, Railway).

---

## 1. Local One-Command Deployment

The fastest way to spin up the entire production-grade stack (PostgreSQL, Redis, Celery Worker, FastAPI Backend, Sandbox Runner, and Next.js Frontend):

```bash
# 1. Clone repository
git clone https://github.com/your-org/questforge.git
cd questforge

# 2. Configure environment variables
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY and HACKERRANK_ACCESS_TOKEN

# 3. Spin up the entire multi-service stack
docker compose up -d --build

# 4. Run database migrations and seed initial rubrics & sample questions
docker compose exec backend-api alembic upgrade head
docker compose exec backend-api python -c "from backend.app.database import SessionLocal; from backend.app.seed.seed_data import seed_initial_data; db = SessionLocal(); seed_initial_data(db); db.close()"
```

Access the applications:
- **Web Frontend**: [http://localhost:3000](http://localhost:3000)
- **FastAPI Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)
- **Prometheus Metrics**: [http://localhost:8000/metrics](http://localhost:8000/metrics)

---

## 2. Production VPS Deployment (Ubuntu / Debian)

### Step 1: Provision Server & Install Docker
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl git ufw fail2ban

# Install Docker Engine
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

### Step 2: Configure Firewall
```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Step 3: Setup Caddy Reverse Proxy with Automatic SSL
Create `/etc/caddy/Caddyfile`:
```caddy
questforge.yourdomain.com {
    reverse_proxy localhost:3000
}

api.questforge.yourdomain.com {
    reverse_proxy localhost:8000
}
```
Reload Caddy:
```bash
sudo systemctl reload caddy
```

---

## 3. Cloud Deployment: Railway & Render

### Railway:
1. Connect your GitHub repository to Railway.
2. Add a **PostgreSQL** database service and a **Redis** service from the Railway Marketplace.
3. Add the **Backend Service**:
   - Dockerfile path: `backend/Dockerfile`
   - Set environment variables (`DATABASE_URL`, `REDIS_URL`, `ANTHROPIC_API_KEY`, `HACKERRANK_ACCESS_TOKEN`).
4. Add the **Celery Worker Service**:
   - Dockerfile path: `backend/Dockerfile`
   - Start command: `celery -A backend.app.workers.celery_app worker --loglevel=info --concurrency=4`
5. Add the **Frontend Service**:
   - Dockerfile path: `frontend/Dockerfile`
   - Set `NEXT_PUBLIC_API_URL` to your backend Railway domain.

---

## 4. Observability & Health Monitoring

QuestForge exposes standard observability endpoints:
- `GET /health`: Returns JSON with status of PostgreSQL connection, Redis connection, and sandbox runner health.
- `GET /metrics`: Returns runtime metrics (total jobs executed, average stage runtimes, pass rates, error counts).
