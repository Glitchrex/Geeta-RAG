import os

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://shikhar:pasword101@localhost:5432/geeta_rag")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "gemma4:latest")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text:latest")

#INGESTION
CHUNK_MAX_CHARS = 1800 
CHUNK_OVERLAP_CHARS = 200
EMBED_BATCH_SIZE = 32

#RAG
TOP_K = 5
NUM_CTX = 8192

#UPLOADS
UPLOAD_DIR = "uploads"
MAX_UPLOAD_MB = 20