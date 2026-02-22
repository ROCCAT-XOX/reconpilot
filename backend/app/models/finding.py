from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.types import GUID, JSON

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.scan import Scan


class Finding(Base):
    __tablename__ = "findings"
    __table_args__ = (
        Index("idx_findings_project_severity", "project_id", "severity"),
        Index("idx_findings_fingerprint", "fingerprint"),
        Index("idx_findings_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        GUID, primary_key=True, default=uuid.uuid4
    )
    scan_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("scans.id", ondelete="CASCADE"), nullable=False
    )
    scan_job_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("scan_jobs.id", ondelete="SET NULL"), nullable=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )

    # Classification
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(10), nullable=False)
    cvss_score: Mapped[Decimal | None] = mapped_column(Numeric(3, 1), nullable=True)
    cvss_vector: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cve_id: Mapped[str | None] = mapped_column(String(20), nullable=True)
    cwe_id: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Target info
    target_host: Mapped[str | None] = mapped_column(String(500), nullable=True)
    target_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_protocol: Mapped[str | None] = mapped_column(String(10), nullable=True)
    target_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    target_service: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Tool info
    source_tool: Mapped[str] = mapped_column(String(50), nullable=False)
    raw_evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Workflow
    status: Mapped[str] = mapped_column(String(20), default="open")
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("users.id"), nullable=True
    )
    verified_by: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("users.id"), nullable=True
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Deduplication
    fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False)
    duplicate_of: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("findings.id"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    project: Mapped[Project] = relationship(back_populates="findings")
    scan: Mapped[Scan] = relationship(back_populates="findings")
    comments: Mapped[list[FindingComment]] = relationship(
        back_populates="finding", cascade="all, delete-orphan"
    )


class FindingComment(Base):
    __tablename__ = "finding_comments"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID, primary_key=True, default=uuid.uuid4
    )
    finding_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("findings.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("users.id"), nullable=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    # Relationships
    finding: Mapped[Finding] = relationship(back_populates="comments")
