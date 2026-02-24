# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ReconForge is a **Reconnaissance Orchestration Platform** for pentesting teams. It orchestrates 18+ open-source security tools in automated pipelines, aggregates results in a central database, and delivers prioritized findings. Internal/proprietary.

## Tech Stack

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Celery, Alembic
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS, TanStack Query, Zustand
- **Database:** PostgreSQL 16 (async via asyncpg), Redis 7 (Celery broker + cache)
- **Infra:** Docker Compose, Nginx reverse proxy, GitHub Actions CI/CD
- **Registry:** `registry.arcadia-capitals.com/reconpilot`
- **Deployment:** k3s cluster, Namespace `flow`, NodePort 30811

## Commands

### Development
```bash
make dev                                        # Full stack Docker (nginx:8080, backend:8000, frontend:5173, postgres:5432, redis:6379)
cd backend && uvicorn app.main:app --reload     # Backend only
cd frontend && npm run dev                      # Frontend only (port 5173)
```

### Testing
```bash
cd backend && .venv/bin/python -m pytest tests/ -v                              # All backend tests
cd backend && .venv/bin/python -m pytest tests/test_scans.py -v                 # Single test file
cd backend && .venv/bin/python -m pytest tests/test_scans.py::TestScanCRUD -v   # Single test class
cd backend && .venv/bin/python -m pytest tests/ -v --cov=app --cov-report=term-missing  # With coverage
make test-docker                                                                # Via Docker
cd frontend && npm run test                                                     # Frontend tests (vitest)
```

Tests use **in-memory SQLite** via aiosqlite (not PostgreSQL). The conftest overrides `DATABASE_URL`, `SECRET_KEY`, `REDIS_URL`, and `ENVIRONMENT`. All tests are async (`asyncio_mode = "auto"`).

### Linting & Formatting
```bash
cd backend && ruff check .       # Backend lint (line-length 100, py312 target)
cd backend && ruff format .      # Backend format
cd frontend && npm run lint      # Frontend lint (eslint)
cd frontend && npm run format    # Frontend format (prettier)
```

### Database
```bash
make migrate                                                    # Run Alembic migrations
make migrate-create MSG="description"                           # Create new migration
make seed                                                       # Seed initial data
make db-shell                                                   # psql into PostgreSQL
```

### Install
```bash
cd backend && pip install -e ".[dev]"   # Backend deps (Python 3.12+)
cd frontend && npm install              # Frontend deps
```

## Architecture

**Monorepo** with `backend/` (Python FastAPI) and `frontend/` (React TypeScript Vite).

### Backend (`backend/app/`)

- **Entry point**: `app/main.py` — mounts all routers under `/api/v1/`
- **Health endpoint**: `/health` (NOT `/api/v1/health`)
- **Config**: `app/config.py` — Pydantic BaseSettings, requires `DATABASE_URL` and `SECRET_KEY`
- **API routes**: `app/api/v1/router.py` — auth, dashboard, users, projects, scope, scans, findings, reports, websocket
- **Auth**: JWT (HS256) with access (30min) + refresh (7day) tokens, bcrypt passwords, Redis-based token blacklist
- **RBAC**: 4 roles (admin > lead > pentester > viewer) with permission sets in `app/api/deps.py`
- **DI shortcuts** in `app/api/deps.py`: `CurrentUser`, `AdminUser`, `LeadOrAdmin`, `PentesterOrAbove`, `DB`, `Pagination`
- **Middleware**: Rate limiting (Redis, fail-open) → Audit logging (all POST/PUT/DELETE to `audit_log` table)
- **CORS**: `redirect_slashes=False` — frontend API calls must be slash-aware

### Scan Orchestration (core domain logic)

- **Tool wrappers** (`app/tools/`): Each tool extends `BaseToolWrapper` with `build_command()` and `parse_output()`. Registered in `tool_registry` dict. Execute via `asyncio.create_subprocess_exec()`.
- **Profiles** (`app/orchestrator/profiles.py`): quick/standard/deep/custom — define ordered phases with tool configs
- **Pipeline engine** (`app/orchestrator/engine.py`): Runs phases sequentially, tools within a phase in parallel. Validates scope, saves ScanJob/Finding records, emits WebSocket events.
- **Chain logic** (`app/orchestrator/chain_logic.py`): Rule-based auto-discovery — feeds tool outputs as new targets into subsequent phases (e.g., subfinder→httpx→nuclei)
- **Scan dispatch** (`app/api/v1/scans.py`): Tries Celery first, falls back to asyncio background task if Redis unavailable

### Security Tools

All wrappers inherit from `backend/app/tools/base.py`, registered in `registry.py`:

| Category | Tools |
|----------|-------|
| **Recon** | Subfinder, Amass, httpx |
| **Scanning** | Nmap, Nuclei, Nikto, ffuf, Gobuster |
| **Web Analysis** | SSLyze, testssl, WhatWeb |
| **Exploitation** | SQLMap |

### Database

- **Models** (`app/models/`): User, Project, ProjectMember, ScopeTarget, Scan, ScanJob, Finding, FindingComment, AuditLog, Report, ScanComparison
- **Custom types** (`app/core/types.py`): `GUID`, `JSON`, `INET` — PostgreSQL-native in prod (UUID, JSONB, INET), SQLite-compatible fallbacks for tests
- **Migrations**: Alembic async in `backend/alembic/`
- **Finding deduplication**: SHA-256 fingerprint over (host, port, url, cve, cwe, title)

### Frontend (`frontend/src/`)

- **Routing**: React Router 6 in `App.tsx` — `/dashboard`, `/projects/:id`, `/scans/:id`, `/findings/:id`, `/reports`, `/team`, `/settings`
- **API client** (`api/client.ts`): Axios with auto Bearer token injection and transparent 401 refresh
- **State**: Zustand stores (`store/`) for auth, notifications, scans. TanStack Query for server state via `hooks/`
- **WebSocket**: Real-time scan progress updates (`api/websocket.ts`, `hooks/useWebSocket.ts`)
- **Vite dev proxy**: `/api` → `http://localhost:8000`
- **Mobile**: Fully responsive (all pages)

## CI/CD Pipeline

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

## Key Patterns

- **Fail-open design**: Redis failures (rate limiting, token blacklist) log warnings but don't block requests
- **Scope enforcement**: All scan targets validated against authorized scope before execution — critical for legal compliance
- **Ruff config**: Extensive per-file-ignores in `pyproject.toml` (subprocess calls in tools, asserts in tests, etc.)
- **Test fixtures**: `conftest.py` provides `client`, `db_session`, `test_user`/`admin_user`/`viewer_user`, `test_project`, `test_scope`, `test_scan`, `test_finding`. Use `auth_header(user)` helper for authenticated requests.

## Code Conventions

- **Python:** Ruff for linting/formatting, type hints everywhere, async-first
- **TypeScript:** ESLint + Prettier, strict mode, interfaces in `src/types/`
- **Git:** Direct pushes to `main`, descriptive commit messages with `feat:`/`fix:`/`docs:` prefixes

## How to Add Things

- **New API endpoint**: Add router in `backend/app/api/v1/`, register in `router.py`
- **New tool**: Create wrapper in `backend/app/tools/<category>/`, register in `registry.py`
- **New page**: Create in `frontend/src/pages/`, add route in `App.tsx`
- **New model**: Create in `backend/app/models/`, import in `__init__.py`, create Alembic migration

## Known Issues

See `TODO.md` for the full roadmap. Key items:
- Scan execution: Celery tasks create DB entries but tool dispatch needs wiring
- Reporting engine (Epic 8) was descoped
- CI needs post-deploy smoke tests
