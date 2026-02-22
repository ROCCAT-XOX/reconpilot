<p align="center">
  <img src="docs/logo.png" alt="ReconForge Logo" width="300">
</p>

# ReconForge

**Reconnaissance Orchestration Platform** for pentesting teams.

ReconForge orchestrates 18+ open-source security tools in automated pipelines, aggregates results in a central database, and delivers prioritized, client-ready reports.

## Quick Start

```bash
# Copy environment template
cp .env.example .env
# Edit .env with your secrets

# Start development environment
make dev

# Run migrations
make migrate

# Seed initial data
make seed
```

## Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md) for the full architecture document.

## Tech Stack

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.0, Celery, Alembic
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS
- **Database:** PostgreSQL 16, Redis 7
- **Infrastructure:** Docker Compose, Nginx

## Development

```bash
# Backend only
cd backend && uvicorn app.main:app --reload

# Frontend only
cd frontend && npm run dev

# Full stack
make dev
```

## Project Structure

```
reconforge/
├── backend/         # FastAPI + SQLAlchemy + Celery
├── frontend/        # React + TypeScript + Vite
├── nginx/           # Reverse proxy config
├── scripts/         # Setup & utility scripts
└── docs/            # Documentation
```

## License

Internal use only. Proprietary.
