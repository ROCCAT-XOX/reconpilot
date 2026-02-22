from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.types import GUID, JSON

if TYPE_CHECKING:
    from app.models.project import Project


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID, primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    scan_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("scans.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    template: Mapped[str] = mapped_column(String(50), default="standard")
    format: Mapped[str] = mapped_column(String(10), default="pdf")
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    generated_by: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    # Relationships
    project: Mapped[Project] = relationship(back_populates="reports")


class ScanComparison(Base):
    __tablename__ = "scan_comparisons"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID, primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    scan_a_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("scans.id"), nullable=True
    )
    scan_b_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("scans.id"), nullable=True
    )
    new_findings: Mapped[int] = mapped_column(Integer, default=0)
    resolved_findings: Mapped[int] = mapped_column(Integer, default=0)
    unchanged_findings: Mapped[int] = mapped_column(Integer, default=0)
    comparison_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
