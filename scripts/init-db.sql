-- Database initialization for mycontextprotocol
-- PostgreSQL 16 with pgvector extension

-- Enable pgvector extension for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Inbox table: temporary storage for incoming memories before processing
CREATE TABLE IF NOT EXISTS inbox (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    source VARCHAR(255) NOT NULL,
    target VARCHAR(50) DEFAULT 'all',
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_inbox_processed ON inbox(processed, created_at);
CREATE INDEX idx_inbox_created_at ON inbox(created_at DESC);

-- Document store: embedded documents with vector representations
CREATE TABLE IF NOT EXISTS document_store (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    embedding vector(768),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_document_store_embedding ON document_store USING hnsw (embedding vector_cosine_ops);
CREATE INDEX idx_document_store_metadata ON document_store USING gin(metadata);
CREATE INDEX idx_document_store_created_at ON document_store(created_at DESC);

-- Mem0 will create its own tables for knowledge graph and facts
-- Those are managed by the mem0-api-server automatically
