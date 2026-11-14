import ollama
import numpy as np

LLM = "gemma4"
EMBED = "nomic-embed-text"

docs = [
    "Our refund policy allows returns within 30 days of purchase.",
    "Support is available Monday to Friday, 9am to 6pm IST.",
    "Premium plan costs 20 rupees"
    "Power is 100"
]

def embed(texts):
    res = ollama.embed(model=EMBED, input=texts)
    return np.array(res["embeddings"])

def cosine(a,b):
    return (a @ b.T) / (np.linalg.norm(a, axis=1)[:, None] * np.linalg.norm(b,axis=1))

doc_vecs = embed(docs)
question = "How much is power?"
q_vec = embed([question])
scores = cosine(q_vec, doc_vecs)[0]
top_k = np.argsort(scores)[::-1][:2]
context = "\n".join(docs[i] for i in top_k)
prompt = f"""Answer using only the context. If unknown, say "I don't know".and

Context: {context}
Question: {question}"""

answer = ollama.chat(model=LLM, messages=[{"role": "user", "content": prompt}])
print("Scores:", scores.round(5))
print("Answer:", answer["message"]["content"])