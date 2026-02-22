#!/bin/bash
set -e

echo "=== ReconForge Starting ==="

# Wait for PostgreSQL
echo "Waiting for PostgreSQL..."
for i in $(seq 1 30); do
    if python3 -c "
import asyncio, sys
sys.path.insert(0, '/app/backend')
async def check():
    from sqlalchemy import text
    from app.core.database import engine
    async with engine.connect() as conn:
        await conn.execute(text('SELECT 1'))
asyncio.run(check())
" 2>/dev/null; then
        echo "PostgreSQL ready."
        break
    fi
    echo "  ...waiting ($i/30)"
    sleep 2
done

# Run Alembic migrations
echo "Running database migrations..."
cd /app/backend
python3 -m alembic upgrade head 2>&1 || {
    echo "Alembic migration failed, attempting table creation..."
    python3 -c "
import asyncio, sys
sys.path.insert(0, '/app/backend')
async def create():
    from app.core.database import engine, Base
    from app.models import *  # noqa: F401,F403
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print('Tables created via metadata.create_all')
asyncio.run(create())
"
}

# Seed admin user if not exists
echo "Checking seed data..."
python3 /app/scripts/seed_db.py 2>&1 || echo "Seed skipped or failed (non-fatal)"

echo "=== Starting services ==="

# Start nginx in background
nginx &

# Start uvicorn
exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2 --app-dir /app/backend
