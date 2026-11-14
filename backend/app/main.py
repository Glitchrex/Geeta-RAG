import json
import logging
import shutil
import time
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import UUID

from fastapi import BackgroundTasks, FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app import config
from app import repository
from app.db import pool
from app.generation import stream_answer
from app.ingest import inges_document
from app.retrieval import search
from app.schemas import ChatRequest, DocumentOut

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger('geeta-rag')

@asynccontextmanager
async def lifespan(app: FastAPI):
    pool.open(wait=True)
    Path(config.UPLOAD_DIR).mkdir(exist_ok=True)
    yield
    pool.close()


app = FastAPI(title="Geeta-RAG", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def server_sent_event(data: object, event: str | None = None) -> str:
    prefix = f"event: {event}\n" if event else ""
    return f"{prefix}data: {json.dumps(data)}\n\n"

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

@app.post("/documents", response_model=DocumentOut, status_code=202)
def upload_document(file: UploadFile, background_tasks: BackgroundTasks):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=415, detail="Only PDF files are supported")
    if file.size and file.size > config.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File is Larger than {config.MAX_UPLOAD_MB} MB")

    document = repository.create_document(file.filename or "document.pdf")
    path = Path(config.UPLOAD_DIR) / f"{document['id']}.pdf"
    with path.open("wb") as out:
        shutil.copyfileobj(file.file,out)

    background_tasks.add_task(inges_document, document["id"], str(path))
    return document

@app.get("/documents/{document_id}", response_model=DocumentOut)
def get_document(document_id: UUID):
    document = repository.get_document(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document

@app.post("/chat")
def chat(request: ChatRequest):
    document = repository.get_document(request.document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    if document["status"] != "done":
        raise HTTPException(status_code=409, detail=f"Document is {document['status']}, not ready")

    started = time.perf_counter()
    chunks = search(request.document_id, request.question, config.TOP_K)
    retrieval_ms = (time.perf_counter() - started) * 1000

    def event_stream():
        sources = [
            {"n": n, "page": c["page"], "preview": c["content"][:200]}
            for n, c in enumerate(chunks, start=1)
        ]
        yield server_sent_event(sources, event="sources")
        try:
            for token in stream_answer(request.question, chunks):
                yield server_sent_event(token)
        except Exception:
            log.exception("Generation Failed")
            yield server_sent_event("Answer generation failed. Check that Ollama is running.", event="error")
        finally:
            total_ms = (time.perf_counter() - started) * 1000
            log.info("chat doc=%s chunks=%d retrieval_ms=%.0f total_ms=%.0f",
                     request.document_id, len(chunks), retrieval_ms, total_ms)
            yield server_sent_event({}, event="done")

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
