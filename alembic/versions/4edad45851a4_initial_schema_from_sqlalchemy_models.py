"""Initial schema from SQLAlchemy models

Revision ID: 4edad45851a4
Revises:
Create Date: 2025-01-06 23:57:15.869113

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = "4edad45851a4"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Create inbox table
    op.create_table(
        "inbox",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.Column(
            "status", sa.String(length=50), server_default=sa.text("'pending'"), nullable=False
        ),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("content_hash"),
    )
    op.create_index("idx_inbox_status", "inbox", ["status"])
    op.create_index("idx_inbox_created_at", "inbox", ["created_at"])

    # Create mem0_user_facts table
    op.create_table(
        "mem0_user_facts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("fact", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("confidence", sa.Float(), server_default=sa.text("1.0"), nullable=False),
        sa.Column("embedding", Vector(768), nullable=True),
        sa.Column("metadata", sa.JSON(), server_default=sa.text("'{}'"), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_mem0_user_facts_user_id", "mem0_user_facts", ["user_id"])
    op.create_index("idx_mem0_user_facts_category", "mem0_user_facts", ["category"])
    op.create_index(
        "idx_mem0_user_facts_embedding",
        "mem0_user_facts",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )
    op.create_index(
        "idx_mem0_user_facts_metadata", "mem0_user_facts", ["metadata"], postgresql_using="gin"
    )

    # Create llamaindex_document_store table
    op.create_table(
        "llamaindex_document_store",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("doc_id", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.Column(
            "content_type", sa.String(length=50), server_default=sa.text("'text'"), nullable=False
        ),
        sa.Column("embedding", Vector(768), nullable=True),
        sa.Column("metadata", sa.JSON(), server_default=sa.text("'{}'"), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("doc_id"),
    )
    op.create_index("idx_llamaindex_document_store_doc_id", "llamaindex_document_store", ["doc_id"])
    op.create_index("idx_llamaindex_document_store_source", "llamaindex_document_store", ["source"])
    op.create_index(
        "idx_llamaindex_document_store_content_type", "llamaindex_document_store", ["content_type"]
    )
    op.create_index(
        "idx_llamaindex_document_store_embedding",
        "llamaindex_document_store",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )
    op.create_index(
        "idx_llamaindex_document_store_metadata",
        "llamaindex_document_store",
        ["metadata"],
        postgresql_using="gin",
    )

    # Create llamaindex_property_graph_nodes table
    op.create_table(
        "llamaindex_property_graph_nodes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("node_id", sa.String(length=255), nullable=False),
        sa.Column("label", sa.String(length=100), nullable=False),
        sa.Column("properties", sa.JSON(), server_default=sa.text("'{}'"), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("node_id"),
    )
    op.create_index(
        "idx_llamaindex_property_graph_nodes_node_id",
        "llamaindex_property_graph_nodes",
        ["node_id"],
    )
    op.create_index(
        "idx_llamaindex_property_graph_nodes_label", "llamaindex_property_graph_nodes", ["label"]
    )
    op.create_index(
        "idx_llamaindex_property_graph_nodes_properties",
        "llamaindex_property_graph_nodes",
        ["properties"],
        postgresql_using="gin",
    )

    # Create llamaindex_property_graph_edges table
    op.create_table(
        "llamaindex_property_graph_edges",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("edge_id", sa.String(length=255), nullable=False),
        sa.Column("source_node_id", sa.String(length=255), nullable=False),
        sa.Column("target_node_id", sa.String(length=255), nullable=False),
        sa.Column("relationship_type", sa.String(length=100), nullable=False),
        sa.Column("properties", sa.JSON(), server_default=sa.text("'{}'"), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("edge_id"),
    )
    op.create_index(
        "idx_llamaindex_property_graph_edges_edge_id",
        "llamaindex_property_graph_edges",
        ["edge_id"],
    )
    op.create_index(
        "idx_llamaindex_property_graph_edges_source",
        "llamaindex_property_graph_edges",
        ["source_node_id"],
    )
    op.create_index(
        "idx_llamaindex_property_graph_edges_target",
        "llamaindex_property_graph_edges",
        ["target_node_id"],
    )
    op.create_index(
        "idx_llamaindex_property_graph_edges_relationship",
        "llamaindex_property_graph_edges",
        ["relationship_type"],
    )
    op.create_index(
        "idx_llamaindex_property_graph_edges_properties",
        "llamaindex_property_graph_edges",
        ["properties"],
        postgresql_using="gin",
    )

    # Create llamaindex_vector_index table
    op.create_table(
        "llamaindex_vector_index",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("doc_id", sa.String(length=255), nullable=False),
        sa.Column("chunk_id", sa.String(length=255), nullable=False),
        sa.Column("embedding", Vector(768), nullable=False),
        sa.Column("metadata", sa.JSON(), server_default=sa.text("'{}'"), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chunk_id"),
    )
    op.create_index("idx_llamaindex_vector_index_doc_id", "llamaindex_vector_index", ["doc_id"])
    op.create_index("idx_llamaindex_vector_index_chunk_id", "llamaindex_vector_index", ["chunk_id"])
    op.create_index(
        "idx_llamaindex_vector_index_embedding",
        "llamaindex_vector_index",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )
    op.create_index(
        "idx_llamaindex_vector_index_metadata",
        "llamaindex_vector_index",
        ["metadata"],
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_table("llamaindex_vector_index")
    op.drop_table("llamaindex_property_graph_edges")
    op.drop_table("llamaindex_property_graph_nodes")
    op.drop_table("llamaindex_document_store")
    op.drop_table("mem0_user_facts")
    op.drop_table("inbox")
    op.execute("DROP EXTENSION IF EXISTS vector")
