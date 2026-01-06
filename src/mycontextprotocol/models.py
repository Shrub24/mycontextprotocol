"""Database models for mycontextprotocol.

SQLAlchemy 2.0 declarative models matching init-db.sql schema.
Source of truth for Alembic migrations.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Float,
    Index,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from pgvector.sqlalchemy import Vector


class Base(DeclarativeBase):
    """Base class for all models."""

    type_annotation_map = {
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


class Mem0UserFact(Base):
    """Subjective information about users (Mem0)."""

    __tablename__ = "mem0_user_facts"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    fact: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str | None] = mapped_column(String(100))
    confidence: Mapped[float] = mapped_column(Float, server_default=text("1.0"))
    embedding: Mapped[list[float] | None] = mapped_column(Vector(768))
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", server_default=text("'{}'"))
    created_at: Mapped[datetime] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))

    __table_args__ = (
        Index("idx_mem0_user_facts_user_id", "user_id"),
        Index("idx_mem0_user_facts_category", "category"),
        Index(
            "idx_mem0_user_facts_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        Index("idx_mem0_user_facts_metadata", "metadata", postgresql_using="gin"),
    )


class LlamaIndexDocumentStore(Base):
    """LlamaIndex document storage (objective facts)."""

    __tablename__ = "llamaindex_document_store"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    doc_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str | None] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(50), server_default=text("'text'"))
    embedding: Mapped[list[float] | None] = mapped_column(Vector(768))
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", server_default=text("'{}'"))
    created_at: Mapped[datetime] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))

    __table_args__ = (
        Index("idx_llamaindex_document_store_doc_id", "doc_id"),
        Index("idx_llamaindex_document_store_source", "source"),
        Index("idx_llamaindex_document_store_content_type", "content_type"),
        Index(
            "idx_llamaindex_document_store_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        Index("idx_llamaindex_document_store_metadata", "metadata", postgresql_using="gin"),
    )


class LlamaIndexPropertyGraphNode(Base):
    """Property graph nodes for entity relationships."""

    __tablename__ = "llamaindex_property_graph_nodes"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    node_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    properties: Mapped[dict[str, Any]] = mapped_column(server_default=text("'{}'"))
    embedding: Mapped[list[float] | None] = mapped_column(Vector(768))
    created_at: Mapped[datetime] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))

    __table_args__ = (
        Index("idx_llamaindex_property_graph_nodes_node_id", "node_id"),
        Index("idx_llamaindex_property_graph_nodes_label", "label"),
        Index(
            "idx_llamaindex_property_graph_nodes_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        Index(
            "idx_llamaindex_property_graph_nodes_properties", "properties", postgresql_using="gin"
        ),
    )


class LlamaIndexPropertyGraphEdge(Base):
    """Property graph edges connecting entities."""

    __tablename__ = "llamaindex_property_graph_edges"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    edge_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    source_node_id: Mapped[str] = mapped_column(String(255), nullable=False)
    target_node_id: Mapped[str] = mapped_column(String(255), nullable=False)
    relationship: Mapped[str] = mapped_column(String(100), nullable=False)
    properties: Mapped[dict[str, Any]] = mapped_column(server_default=text("'{}'"))
    created_at: Mapped[datetime] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))

    __table_args__ = (
        Index("idx_llamaindex_property_graph_edges_edge_id", "edge_id"),
        Index("idx_llamaindex_property_graph_edges_source_node_id", "source_node_id"),
        Index("idx_llamaindex_property_graph_edges_target_node_id", "target_node_id"),
        Index("idx_llamaindex_property_graph_edges_relationship", "relationship"),
        Index(
            "idx_llamaindex_property_graph_edges_properties", "properties", postgresql_using="gin"
        ),
    )


class LlamaIndexVectorIndex(Base):
    """Vector index for semantic search."""

    __tablename__ = "llamaindex_vector_index"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    doc_id: Mapped[str] = mapped_column(String(255), nullable=False)
    chunk_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(768), nullable=False)
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", server_default=text("'{}'"))
    created_at: Mapped[datetime] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))

    __table_args__ = (
        Index("idx_llamaindex_vector_index_doc_id", "doc_id"),
        Index("idx_llamaindex_vector_index_chunk_id", "chunk_id"),
        Index(
            "idx_llamaindex_vector_index_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        Index("idx_llamaindex_vector_index_metadata", "metadata", postgresql_using="gin"),
    )
