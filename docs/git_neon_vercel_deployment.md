# QuestForge: Git + Neon + Vercel Production Deployment Guide

This guide details the complete deployment workflow for **QuestForge** using **Git (GitHub)**, **Neon (Serverless PostgreSQL)**, and **Vercel (Next.js & Serverless FastAPI)**.

---

## 1. Architecture Topology

```
+-------------------------------------------------------------------------+
|                               GitHub Repo                               |
|   (Codebase, Prompts, Next.js Frontend, FastAPI Backend, CI/CD)         |
+-----------------------------------+-------------------------------------+
                                    |
            Push to main / Git Sync | Auto-Deploy
                                    v
+-------------------------------------------------------------------------+
|                           Vercel Platform                               |
|                                                                         |
|   +---------------------------------+  +----------------------------+   |
|   |       Next.js 14 Web App        |  |  FastAPI Serverless App    |   |
|   |  - Dashboard & Review Queue     |  |  - Auth & JWT Guard        |   |
|   |  - Publishing & History UI      |  |  - 7-Stage Pipeline Engine |   |
|   |  - Edge CDN cached static assets|  |  - HackerRank Client       |   |
|   +----------------+----------------+  +--------------+-------------+   |
|                    |                                  |                 |
+--------------------|----------------------------------|-----------------+
                     |                                  |
                     | Direct API requests              | Pooled SSL Connection
                     v                                  v
+-------------------------------------------------------------------------+
|                       Neon Serverless PostgreSQL                        |
|                                                                         |
|   - Compute autoscaling & scale-to-zero                                 |
|   - Built-in PgBouncer connection pooler                                |
|   - Instant database branching for staging and preview deployments      |
+-------------------------------------------------------------------------+
```

---

## 2. Neon Serverless PostgreSQL Setup

### 2.1 Retrieve Your Connection String
In the [Neon Console](https://console.neon.tech):
1. Navigate to your project dashboard.
2. Under **Connection Details**, select **Pooled connection**.
3. Copy the pooled PostgreSQL connection string. It will look like:
   ```text
   postgresql://<user>:<password>@<ep-identifier>-pooler.<region>.aws.neon.tech/neondb?sslmode=require
   ```

### 2.2 Configure Local & CI Environment Variables
In your local `.env` or CI runner:
```bash
USE_NEON=true
DATABASE_URL=postgresql://<user>:<password>@<ep-identifier>-pooler.<region>.aws.neon.tech/neondb?sslmode=require
```

### 2.3 Run Alembic Migrations on Neon
To create all tables, indexes, and relations on Neon:
```bash
# Set USE_NEON flag and run migration
python -m alembic -c backend/alembic.ini upgrade head
```

### 2.4 Seed Initial Production Data
Populate Neon with difficulty rubrics, admin/reviewer users, and 9 verified challenges:
```bash
python -c "from backend.app.database import SessionLocal; from backend.app.seed.seed_data import seed_initial_data; db = SessionLocal(); seed_initial_data(db); db.close(); print('Neon seeded successfully!')"
```

---

## 3. Git Repository Preparation & Committing

### 3.1 Check Git Status
Ensure only QuestForge application files are staged:
```bash
git status -s
```

### 3.2 Add and Commit Changes
```bash
# Stage all QuestForge files
git add .

# Create production release commit
git commit -m "feat: QuestForge AI question engine with Neon and Vercel deployment"

# Push to your GitHub main branch
git push origin main
```

---

## 4. Vercel Deployment

### Method A: Deploy via Vercel Dashboard (GitHub Integration)

1. Open [vercel.com](https://vercel.com) and click **"Add New Project"**.
2. Select and import your GitHub repository.
3. Configure the **Build & Development Settings**:
   - **Framework Preset**: Next.js
   - **Root Directory**: Leave as `.` (or set to `frontend` if deploying frontend separately)
4. Add the **Environment Variables** in the Vercel project settings:

| Variable Name | Value | Description |
| :--- | :--- | :--- |
| `DATABASE_URL` | `postgresql://...@...-pooler...neon.tech/neondb?sslmode=require` | Pooled Neon PostgreSQL connection string |
| `USE_NEON` | `true` | Activates Neon database mode |
| `ANTHROPIC_API_KEY` | `sk-ant-api03-...` | Anthropic Claude API Key |
| `ANTHROPIC_MODEL` | `claude-3-5-sonnet-20241022` | Generation model |
| `HACKERRANK_ACCESS_TOKEN` | `your_token_here` | HackerRank for Work Bearer token |
| `HACKERRANK_DRY_RUN` | `false` | Set `true` for dry-run testing |
| `SECRET_KEY` | `<secure-random-32-byte-hex-string>` | JWT authentication secret |
| `SANDBOX_TYPE` | `subprocess` | Execution runner for serverless environments |
| `NEXT_PUBLIC_API_URL` | `https://your-project.vercel.app` | Base URL for API calls |

5. Click **"Deploy"**. Vercel will build your Next.js frontend and Python serverless endpoints.

---

### Method B: Deploy via Vercel CLI

```bash
# Install Vercel CLI
npm install -g vercel

# Authenticate with Vercel
vercel login

# Link and deploy project
vercel

# Deploy to production
vercel --prod
```

---

## 5. Live Production Verification

Once deployed on Vercel with Neon DB:

1. **Check Backend Health**:
   Visit `https://<your-vercel-domain>/health`
   Expected response:
   ```json
   {
     "status": "healthy",
     "service": "QuestForge",
     "environment": "production",
     "database": "connected"
   }
   ```

2. **Check Seeded Challenges**:
   Visit `https://<your-vercel-domain>/questions`
   Expected response: JSON array of 4+ pre-seeded questions across Arrays, Dynamic Programming, and Graphs.

3. **Log in to Frontend**:
   Navigate to `https://<your-vercel-domain>`:
   - Use default reviewer credentials:
     - **Email**: `reviewer@questforge.io`
     - **Password**: `QuestForgeReview2026!`

4. **Launch an AI Generation Job**:
   - Select Topic: *Dynamic Programming*, Subtopic: *Longest Palindromic Subsequence*.
   - Click **"Launch Question Generation Job"**.
   - Monitor live stage progress: Spec $\to$ Generate $\to$ Test Cases $\to$ Verification $\to$ Quality Critic $\to$ Dedup $\to$ Persist.
   - Inspect the newly generated question in the Review Queue.
   - Click **"Publish to HackerRank"** or download the **HackerRank Challenge ZIP package**.
