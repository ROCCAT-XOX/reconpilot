"""Portable SQLAlchemy column types that work with both PostgreSQL and SQLite."""

import json
import uuid

from sqlalchemy import String, Text, TypeDecorator
from sqlalchemy.dialects.postgresql import INET as PG_INET
from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.config import settings

_is_sqlite = settings.DATABASE_URL.startswith("sqlite")


class GUID(TypeDecorator):
    """Platform-independent UUID type. Uses PG UUID on Postgres, CHAR(36) on SQLite."""
    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value if isinstance(value, uuid.UUID) else uuid.UUID(value)
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, uuid.UUID):
            return uuid.UUID(str(value))
        return value


class JSON(TypeDecorator):
    """Platform-independent JSON type.
    Uses JSONB on Postgres, TEXT with JSON serialization on SQLite."""
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_JSONB)
        return dialect.type_descriptor(Text)

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name != "postgresql":
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if dialect.name != "postgresql" and isinstance(value, str):
            return json.loads(value)
        return value


class INET(TypeDecorator):
    """Platform-independent INET type. Uses INET on Postgres, VARCHAR on SQLite."""
    impl = String(45)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_INET)
        return dialect.type_descriptor(String(45))
