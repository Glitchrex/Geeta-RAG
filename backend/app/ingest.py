import logging
from uuid import UUID
from app import config, repository
from app.chunker import chunk_text
from app.embeddings import embed_documents
from app.parser import parse_pdf

log = logging.getLogger(__name__)

def inges_document(document_id: UUID, path: str) -> None:
    """Parse -> Chunk -> embed -> store. Runs in the background after upload."""
    try:
        repository.set_status(document_id, "processing")

        records = []
        for page, page_text in parse_pdf(path):
            for chunk in chunk_text(page_text, config.CHUNK_MAX_CHARS, config.CHUNK_OVERLAP_CHARS):
                records.append({"page": page, "chunk_index": len(records), "content": chunk})

        if not records:
            raise ValueError("No text found. Scanned PDFs need OCR.")

        for start in range(0, len(records), config.EMBED_BATCH_SIZE):
            batch = records[start:start + config.EMBED_BATCH_SIZE]
            vectors = embed_documents([r["content"] for r in batch])
            for record, vector in zip(batch, vectors, strict= True):
                record["embedding"] = vector
            repository.set_progress(document_id, start + len(batch), len(records))


        repository.replace_chunks(document_id, records)
        repository.set_status(document_id, "done")
        log.info("Ingested %s : %d chunks", document_id, len(records))
    except Exception as exeption:
        log.exception("Ingest failed for %s", document_id)
        repository.set_status(document_id, "failed", str(exeption))

