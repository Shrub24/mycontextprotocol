"""Database models for mycontextprotocol.

SQLAlchemy 2.0 declarative models for application-managed tables.
Source of truth for Alembic migrations.

Note: Mem0 and LlamaIndex manage their own tables:
- Mem0: Creates 'mem0' table (id, vector, payload) via pgvector provider
- LlamaIndex: Creates 'data_<table_name>' tables via PGVectorStore
- PropertyGraph: Uses SimplePropertyGraphStore (disk-based, future: Neo4j)
"""

from datetime import datetime
from typing import Any, ClassVar
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Index,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all models."""

    type_annotation_map: ClassVar[dict[type, Any]] = {
        datetime: TIMESTAMP(timezone=True),
        dict[str, Any]: JSONB,
    }


class Inbox(Base):
    """Temporary storage for incoming data before processing."""

    __tablename__ = "inbox"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    target: Mapped[str] = mapped_column(String(50), server_default=text("'all'"))
    processed: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))
    processed_at: Mapped[datetime | None] = mapped_column(default=None)

    __table_args__ = (
        Index("idx_inbox_processed", "processed", "created_at"),
        Index("idx_inbox_created_at", "created_at", postgresql_ops={"created_at": "DESC"}),
        Index(
            "idx_inbox_content_hash",
            "content_hash",
            unique=True,
            postgresql_where=text("processed = false"),
        ),
    )
