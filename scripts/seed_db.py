#!/usr/bin/env python3
"""Seed the database with an initial admin user.

⚠️  DEV/SETUP ONLY — Do not run in production without changing the password.
Override the default password via the SEED_ADMIN_PASSWORD environment variable.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.core.database import engine, async_session, Base
from app.core.security import hash_password
from app.models.user import User
from app.models.project import Project
from app.models.scope import ScopeTarget
from app.models.scan import Scan, ScanJob
from app.models.finding import Finding, FindingComment
from app.models.audit_log import AuditLog
from app.models.report import Report, ScanComparison
from sqlalchemy import select


async def seed():
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        # Check if admin already exists
        result = await session.execute(select(User).where(User.email == "admin@reconforge.local"))
        if result.scalar_one_or_none():
            print("Admin user already exists, skipping.")
            return

        password = os.environ.get("SEED_ADMIN_PASSWORD", "ReconForge2026!")
        admin = User(
            email="admin@reconforge.local",
            hashed_password=hash_password(password),
            full_name="System Administrator",
            role="admin",
            is_active=True,
        )
        session.add(admin)
        await session.commit()
        print(f"Created admin user: admin@reconforge.local (ID: {admin.id})")
        print(f"Password: {password}")
        print("\n⚠️  DEV ONLY — Change this password immediately in production!")


if __name__ == "__main__":
    asyncio.run(seed())
