-- Database initialization for mycontextprotocol
-- PostgreSQL 18 with pgvector extension
-- Architecture: CloudNativePG + Mem0 + LlamaIndex

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- APPLICATION TABLES
-- ============================================================================

-- Inbox: temporary storage for incoming data before processing
CREATE TABLE IF NOT EXISTS inbox (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    source VARCHAR(255) NOT NULL,
    target VARCHAR(50) DEFAULT 'all',
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_inbox_processed ON inbox(processed, created_at);
CREATE INDEX idx_inbox_created_at ON inbox(created_at DESC);
CREATE UNIQUE INDEX idx_inbox_content_hash ON inbox(content_hash) WHERE NOT processed;

-- ============================================================================
-- MEM0 TABLES (Subjective Memory - User Preferences & Opinions)
-- ============================================================================

-- User facts: subjective information about users
CREATE TABLE IF NOT EXISTS mem0_user_facts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    fact TEXT NOT NULL,
    category VARCHAR(100),
    confidence FLOAT DEFAULT 1.0,
    embedding vector(768),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_mem0_user_facts_user_id ON mem0_user_facts(user_id);
CREATE INDEX idx_mem0_user_facts_category ON mem0_user_facts(category);
CREATE INDEX idx_mem0_user_facts_embedding ON mem0_user_facts USING hnsw (embedding vector_cosine_ops);
CREATE INDEX idx_mem0_user_facts_metadata ON mem0_user_facts USING gin(metadata);

-- Memory index: episodic memory timeline
CREATE TABLE IF NOT EXISTS mem0_memory_index (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    memory_type VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    embedding vector(768),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_mem0_memory_index_user_id ON mem0_memory_index(user_id);
CREATE INDEX idx_mem0_memory_index_type ON mem0_memory_index(memory_type);
CREATE INDEX idx_mem0_memory_index_embedding ON mem0_memory_index USING hnsw (embedding vector_cosine_ops);
CREATE INDEX idx_mem0_memory_index_created_at ON mem0_memory_index(created_at DESC);

-- ============================================================================
-- LLAMAINDEX TABLES (Objective Knowledge - Facts & Documents)
-- ============================================================================

-- Document store: source documents with embeddings
CREATE TABLE IF NOT EXISTS llamaindex_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_id VARCHAR(255) UNIQUE NOT NULL,
    content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    embedding vector(768),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_llamaindex_documents_doc_id ON llamaindex_documents(doc_id);
CREATE INDEX idx_llamaindex_documents_embedding ON llamaindex_documents USING hnsw (embedding vector_cosine_ops);
CREATE INDEX idx_llamaindex_documents_metadata ON llamaindex_documents USING gin(metadata);
CREATE UNIQUE INDEX idx_llamaindex_documents_content_hash ON llamaindex_documents(content_hash);

-- Knowledge graph nodes
CREATE TABLE IF NOT EXISTS llamaindex_kg_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    node_id VARCHAR(255) UNIQUE NOT NULL,
    node_type VARCHAR(100) NOT NULL,
    properties JSONB DEFAULT '{}',
    embedding vector(768),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_llamaindex_kg_nodes_node_id ON llamaindex_kg_nodes(node_id);
CREATE INDEX idx_llamaindex_kg_nodes_type ON llamaindex_kg_nodes(node_type);
CREATE INDEX idx_llamaindex_kg_nodes_properties ON llamaindex_kg_nodes USING gin(properties);
CREATE INDEX idx_llamaindex_kg_nodes_embedding ON llamaindex_kg_nodes USING hnsw (embedding vector_cosine_ops);

-- Knowledge graph edges
CREATE TABLE IF NOT EXISTS llamaindex_kg_edges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_node_id VARCHAR(255) NOT NULL,
    target_node_id VARCHAR(255) NOT NULL,
    edge_type VARCHAR(100) NOT NULL,
    properties JSONB DEFAULT '{}',
    weight FLOAT DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_node_id) REFERENCES llamaindex_kg_nodes(node_id) ON DELETE CASCADE,
    FOREIGN KEY (target_node_id) REFERENCES llamaindex_kg_nodes(node_id) ON DELETE CASCADE
);

CREATE INDEX idx_llamaindex_kg_edges_source ON llamaindex_kg_edges(source_node_id);
CREATE INDEX idx_llamaindex_kg_edges_target ON llamaindex_kg_edges(target_node_id);
CREATE INDEX idx_llamaindex_kg_edges_type ON llamaindex_kg_edges(edge_type);
CREATE INDEX idx_llamaindex_kg_edges_properties ON llamaindex_kg_edges USING gin(properties);
CREATE UNIQUE INDEX idx_llamaindex_kg_edges_unique ON llamaindex_kg_edges(source_node_id, target_node_id, edge_type);
