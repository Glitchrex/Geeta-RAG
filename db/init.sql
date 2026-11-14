CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename text NOT NULL,
    status text NOT NULL DEFAULT 'pending' check (status IN ('pending','done','failed','processing')),
    error text,
    total_chunks INT NOT NULL DEFAULT 0,
    embedded_chunks INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS chunks ( 
    id BIGSERIAL PRIMARY KEY,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE, -- Delete cascade means primary key. delete foriegn key with it
    chunk_index INT NOT NULL,
    page INT NOT NULL,
    content TEXT NOT NULL,
    embedding vector(768) NOT NULL,
    content_tsv tsvector GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
    UNIQUE (document_id, chunk_index)
);

-- HNSW = Hierarchical Navigable Small World used to find nearest neighbour fast using ANN (Approxiamate Nearest Neighbour)
CREATE INDEX IF NOT EXISTS chunks_embedding_hnsw ON chunks USING hnsw (embedding vector_cosine_ops);

-- GIN = Generalized Inverted Index used to find text search fast using full text search
CREATE INDEX IF NOT EXISTS chunks_content_tsv_gin ON chunks USING gin (content_tsv);