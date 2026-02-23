"""Shared fixtures for the ReconForge test suite."""

import os
import uuid

# Override settings BEFORE any app imports
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-not-for-production-use-1234567890"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["ENVIRONMENT"] = "testing"

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.finding import Finding, FindingComment
from app.models.project import Project
from app.models.report import Report, ScanComparison
from app.models.scan import Scan, ScanJob
from app.models.scope import ScopeTarget
from app.models.user import ProjectMember, User

# In-memory SQLite engine for tests
test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Create all tables before each test, drop after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    """Provide a test database session."""
    async with TestSessionLocal() as session:
        yield session


async def _override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


app.dependency_overrides[get_db] = _override_get_db


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    """Provide an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create and return a test user (pentester role)."""
    user = User(
        id=uuid.uuid4(),
        email="testuser@example.com",
        hashed_password=hash_password("TestPassword123!"),
        full_name="Test User",
        role="pentester",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create and return an admin user."""
    user = User(
        id=uuid.uuid4(),
        email="admin@example.com",
        hashed_password=hash_password("AdminPassword123!"),
        full_name="Admin User",
        role="admin",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def viewer_user(db_session: AsyncSession) -> User:
    """Create and return a viewer user."""
    user = User(
        id=uuid.uuid4(),
        email="viewer@example.com",
        hashed_password=hash_password("ViewerPassword123!"),
        full_name="Viewer User",
        role="viewer",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


def auth_header(user: User) -> dict:
    """Generate an Authorization header for the given user."""
    token = create_access_token(str(user.id), user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def test_project(db_session: AsyncSession, test_user: User) -> Project:
    """Create a test project with the test user as a member."""
    project = Project(
        id=uuid.uuid4(),
        name="Test Project",
        client_name="Test Client",
        description="A test project",
        status="active",
        created_by=test_user.id,
    )
    db_session.add(project)
    await db_session.flush()

    member = ProjectMember(
        project_id=project.id,
        user_id=test_user.id,
        role="lead",
    )
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest_asyncio.fixture
async def test_scope(db_session: AsyncSession, test_project: Project, test_user: User) -> ScopeTarget:
    """Create a scope target for the test project."""
    scope = ScopeTarget(
        project_id=test_project.id,
        target_type="domain",
        target_value="example.com",
        is_excluded=False,
        added_by=test_user.id,
    )
    db_session.add(scope)
    await db_session.commit()
    await db_session.refresh(scope)
    return scope


@pytest_asyncio.fixture
async def test_scan(db_session: AsyncSession, test_project: Project, test_user: User) -> Scan:
    """Create a test scan."""
    scan = Scan(
        id=uuid.uuid4(),
        project_id=test_project.id,
        name="Test Scan",
        profile="quick",
        config={},
        started_by=test_user.id,
        status="completed",
    )
    db_session.add(scan)
    await db_session.commit()
    await db_session.refresh(scan)
    return scan


@pytest_asyncio.fixture
async def test_finding(db_session: AsyncSession, test_project: Project, test_scan: Scan) -> Finding:
    """Create a test finding."""
    finding = Finding(
        id=uuid.uuid4(),
        scan_id=test_scan.id,
        project_id=test_project.id,
        title="Test XSS Vulnerability",
        description="Reflected XSS in search parameter",
        severity="high",
        target_host="example.com",
        target_port=443,
        target_url="https://example.com/search?q=test",
        source_tool="nuclei",
        fingerprint="abc123def456",
        status="open",
    )
    db_session.add(finding)
    await db_session.commit()
    await db_session.refresh(finding)
    return finding
