-- Cortex AI: Week 3-4 document processing and semantic search
-- Requires PostgreSQL + pgvector.

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY,
    owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL CHECK (file_type IN ('pdf', 'docx', 'txt')),
    file_path TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'processing'
        CHECK (status IN ('processing', 'ready', 'failed')),
    page_count INTEGER,
    error_message TEXT,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_documents_owner_id
    ON documents(owner_id);

CREATE INDEX IF NOT EXISTS idx_documents_status
    ON documents(status);

CREATE TABLE IF NOT EXISTS chunks (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    token_count INTEGER NOT NULL,
    embedding vector(1536),
    embedding_status TEXT NOT NULL DEFAULT 'pending'
        CHECK (embedding_status IN ('pending', 'ready', 'failed')),
    embedding_attempts INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chunks_document_id
    ON chunks(document_id);

CREATE INDEX IF NOT EXISTS idx_chunks_embedding_status
    ON chunks(embedding_status);

-- Vector similarity index required by the task.
CREATE INDEX IF NOT EXISTS idx_chunks_embedding_cosine
    ON chunks USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Allow the Week 2 application user to work with the new tables.
GRANT USAGE ON SCHEMA public TO cortex_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE documents, chunks TO cortex_app;
