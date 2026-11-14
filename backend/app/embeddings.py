import numpy as np
from ollama import Client
from app import config

client = Client(host=config.OLLAMA_HOST)

def _embed(texts:list[str]) -> list[np.ndarray]:
    response = client.embed(model = config.EMBED_MODEL, input=texts)
    return [np.asarray(vector, dtype=np.float32) for vector in response["embeddings"]]

def embed_documents(texts: list[str]) -> list[np.ndarray]:
    return _embed([f"search_document: {text}" for text in texts])

def embed_query(text:str) -> np.ndarray:
    return _embed([f"search_query: {text}"])[0]