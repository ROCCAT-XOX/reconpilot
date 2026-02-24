# CLAUDE.md — ReconForge Project Guide

## What is this?

ReconForge is a **Reconnaissance Orchestration Platform** for pentesting teams. It orchestrates 18+ open-source security tools in automated pipelines, aggregates results in a central database, and delivers prioritized findings.

## Tech Stack

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Celery, Alembic
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS, Zustand (state)
- **Database:** PostgreSQL 16 (async via asyncpg), Redis 7 (Celery broker + cache)
- **Infra:** Docker Compose, Nginx reverse proxy, GitHub Actions CI/CD
- **Registry:** `registry.arcadia-capitals.com/reconpilot`
- **Deployment:** k3s cluster, Namespace `flow`, NodePort 30811

## Project Structure

```
reconforge/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # REST endpoints (auth, projects, scans, findings, dashboard, reports, scope, users)
│   │   ├── api/middleware/   # Audit logging, rate limiting
│   │   ├── api/deps.py      # Dependency injection (auth, DB session)
│   │   ├── core/            # database.py, security.py, redis.py, events.py, types.py
│   │   ├── models/          # SQLAlchemy models (user, project, scan, finding, scope, report, audit_log)
│   │   ├── services/        # Business logic (finding_service, scope_validator)
│   │   ├── orchestrator/    # Scan engine, chain_logic, profiles
│   │   ├── tools/           # Security tool wrappers (see below)
│   │   ├── reporting/       # Report generation
│   │   ├── config.py        # Pydantic settings
│   │   └── main.py          # FastAPI app entry point
│   ├── tests/               # pytest tests (84+ tests)
│   ├── alembic.ini
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── pages/           # Dashboard, Projects, Scans, Findings, Reports, Team, Settings, Login
│   │   ├── components/      # layout/, common/, scans/, findings/, network/
│   │   ├── store/           # Zustand stores (auth, scan, notification)
│   │   └── types/           # TypeScript interfaces
│   ├── vite.config.ts
│   └── package.json
├── nginx/                   # Reverse proxy configs
├── scripts/                 # backup.sh, docker-entrypoint.sh, seed_db.py
├── docker-compose.yml       # Production
├── docker-compose.dev.yml   # Development overlay
├── k3s.yaml                 # Kubernetes manifest
├── Makefile                 # Common commands
├── .env.example             # Environment template
└── ARCHITECTURE.md          # Full architecture document
```

## Security Tools (Wrappers)

All tool wrappers inherit from `backend/app/tools/base.py`:

| Category | Tools |
|----------|-------|
| **Recon** | Subfinder, Amass, httpx |
| **Scanning** | Nmap, Nuclei, Nikto, ffuf, Gobuster |
| **Web Analysis** | SSLyze, testssl, WhatWeb |
| **Exploitation** | SQLMap |

Tool registry: `backend/app/tools/registry.py`

## Development Commands

```bash
# Full stack (Docker)
make dev                    # Start dev environment
make up                     # Start production
make down                   # Stop all

# Database
make migrate                # Run Alembic migrations
make migrate-create MSG="x" # Create new migration
make seed                   # Seed initial data

# Testing
make test                   # Backend tests (local venv)
make test-docker            # Backend tests (Docker)
make test-cov               # Tests with coverage

# Code Quality
make lint                   # Ruff (backend) + ESLint (frontend)
make format                 # Auto-format

# Shells
make backend-shell          # Bash into backend container
make db-shell               # psql into PostgreSQL
make redis-cli              # Redis CLI
```

## Backend Specifics

- **Entry point:** `backend/app/main.py`
- **API prefix:** `/api/v1` (configured via `API_V1_PREFIX`)
- **Health endpoint:** `/health` (NOT `/api/v1/health`)
- **Router:** `backend/app/api/v1/router.py` registers all endpoint routers
- **WebSocket:** `backend/app/api/v1/websocket.py` for live scan updates
- **Auth:** JWT-based, `python-jose` + `passlib[bcrypt]`
- **CORS:** `redirect_slashes=False`, `allow_origins=*` (development)
- **Async:** Full async stack — asyncpg, SQLAlchemy async sessions

## Frontend Specifics

- **Dev server:** `npm run dev` (Vite, port 5173)
- **State management:** Zustand (`src/store/`)
- **Routing:** React Router
- **API calls:** Always include trailing slash awareness — backend has `redirect_slashes=False`
- **Mobile:** Fully responsive (all pages)

## CI/CD Pipeline (GitHub Actions)

`.github/workflows/deploy.yml` — triggered on push to `main`:

1. **Lint:** `ruff check backend/`
2. **Test:** pytest against PostgreSQL 16 + Redis 7 service containers
3. **Build & Push:** Docker image → `registry.arcadia-capitals.com/reconpilot`
4. **Deploy:** SSH into k3s node, pull image, restart pod

## Environment Variables

Copy `.env.example` → `.env`. Key variables:
- `DATABASE_URL` — PostgreSQL connection string (asyncpg)
- `REDIS_URL` — Redis connection string
- `SECRET_KEY` — JWT signing key (generate with `openssl rand -hex 32`)
- `ENVIRONMENT` — `development` | `testing` | `production`
- Optional: `WPSCAN_API_TOKEN`, `SHODAN_API_KEY`, `CENSYS_API_ID/SECRET`, `VIRUSTOTAL_API_KEY`

## Known Issues & TODOs

See `TODO.md` for the full roadmap. Key items:
- Scan execution: Celery tasks create DB entries but tool dispatch needs wiring
- Auto-Discover backend logic not yet implemented
- Reporting engine (Epic 8) was descoped
- CI needs post-deploy smoke tests

## Code Conventions

- **Python:** Ruff for linting/formatting, type hints everywhere, async-first
- **TypeScript:** ESLint + Prettier, strict mode, interfaces in `src/types/`
- **Git:** Direct pushes to `main`, descriptive commit messages with `feat:/fix:/docs:` prefixes
- **Testing:** pytest + pytest-asyncio, conftest.py provides fixtures (test DB, test client, auth tokens)

## Architecture Decisions

- **Monorepo:** Single repo for backend + frontend + infra — simplifies CI/CD
- **Async-first:** FastAPI + asyncpg for high concurrency during parallel scans
- **Tool isolation:** Each tool wrapper is independent, registered via `registry.py`
- **Chain logic:** `orchestrator/chain_logic.py` handles intelligent tool chaining (e.g., subfinder → httpx → nuclei)
- **Scan profiles:** Predefined scan configurations in `orchestrator/profiles.py`

## Useful Paths

- API router registration: `backend/app/api/v1/router.py`
- Add new tool: Create wrapper in `backend/app/tools/<category>/`, register in `registry.py`
- Add new page: Create in `frontend/src/pages/`, add route in `App.tsx`
- Add new model: Create in `backend/app/models/`, import in `__init__.py`, create Alembic migration
