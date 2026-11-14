from uuid import UUID
from app.db import pool

def create_document(filename: str) -> dict:
    with pool.connection() as conn:
          return  conn.execute(
                "INSERT INTO documents (filename) VALUES (%s) RETURNING *",
                (filename,),
            ).fetchone()

def get_document(document_id: UUID) -> dict | None:
    with pool.connection() as conn:
        return conn.execute(
            "SELECT * FROM documents WHERE id = %s", (document_id,)
        ).fetchone()

def set_status(document_id: UUID, status: str, error: str | None = None) -> None:
    with pool.connection() as conn:
        conn.execute(
            "UPDATE documents SET status = %s, error = %s WHERE id = %s",
            (status, error, document_id)
        )

def set_progress(document_id: UUID, embedded: int, total: int) -> None:
    with pool.connection() as conn:
        conn.execute(
            "UPDATE documents SET embedded_chunks = %s, total_chunks = %s WHERE id = %s",
            (embedded, total, document_id)
        )

def replace_chunks(document_id: UUID, records: list[dict]) -> None:
    rows = [
        (document_id, r["chunk_index"],r["page"],r["content"],r["embedding"]) 
        for r in records
    ]
    with pool.connection() as conn, conn.transaction(), conn.cursor() as cur:
        cur.execute("DELETE FROM chunks WHERE document_id = %s", (document_id,))
        cur.executemany(
            "INSERT INTO chunks (document_id, chunk_index, page, content, embedding) VALUES (%s,%s,%s,%s,%s)",
            rows
        )