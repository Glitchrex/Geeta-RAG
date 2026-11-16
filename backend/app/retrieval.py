from uuid import UUID
from app.db import pool
from app.embeddings import embed_query

VECTOR_SQL = """
SELECT id, page, chunk_index, content,
       1 - (embedding <=> %(qvec)s) AS score
FROM chunks
WHERE document_id = %(doc_id)s
ORDER BY embedding <=> %(qvec)s
LIMIT %(k)s
"""

HYBRID_SQL = """
with q AS (
    SELECT replace(plainto_tsquery('simple',%(qtext)s)::text, '&', '|')::tsquery AS query),
    semantic AS (
        SELECT id, 
            ROW_NUMBER() OVER (ORDER BY embedding <=> %(qvec)s) AS rank
        From  chunks
        WHERE document_id = %(doc_id)s
        ORDER BY embedding <=> %(qvec)s
        LIMIT 20
    ),
    keyword AS (
        SELECT c.id,
            ROW_NUMBER() OVER (ORDER BY ts_rank_cd(c.content_tsv, q.query) DESC) AS rank
        FROM chunks c,q
        WHERE c.document_id = %(doc_id)s AND c.content_tsv @@ q.query
        ORDER BY ts_rank_cd(c.content_tsv, q.query) DESC
        LIMIT 20
        )

    SELECT c.id, c.page, c.chunk_index, c.content,
        (COALESCE(1.0 / (60 + sem.rank), 0) + COALESCE(1.0 / (60 + kw.rank), 0))::float
    AS score
    FROM semantic sem
    FULL OUTER JOIN keyword kw ON sem.id = kw.id
    JOIN chunks c ON c.id = COALESCE(sem.id, kw.id)
    ORDER BY score DESC
    LIMIT %(k)s
    """

def search(document_id: UUID, question: str, k: int, hybrid: bool = True) -> list[dict]:
    params = {"qvec": embed_query(question), "doc_id": document_id, "qtext": question, "k": k}
    with pool.connection() as conn:
        return conn.execute(HYBRID_SQL if hybrid else VECTOR_SQL, params).fetchall()