from pathlib import Path
import json
from typing import List, Dict, Any

import chromadb
from sentence_transformers import SentenceTransformer

CHUNKS_FILE = Path("data/processed/chunks.jsonl")
CHROMA_DIR = Path("data/chroma_db")
COLLECTION_NAME = "asu_cs_unofficial_guide"
MODEL_NAME = "all-MiniLM-L6-v2"


def load_chunks() -> List[Dict[str, Any]]:
    """
    Loads processed chunks from data/processed/chunks.jsonl.
    """
    if not CHUNKS_FILE.exists():
        raise FileNotFoundError(
            f"{CHUNKS_FILE} not found. Run `python src/ingest.py` first."
        )

    chunks = []
    with CHUNKS_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                chunks.append(json.loads(line))

    if not chunks:
        raise ValueError("No chunks found in chunks.jsonl.")

    return chunks


def get_model() -> SentenceTransformer:
    """
    Loads the local sentence-transformers embedding model.
    """
    return SentenceTransformer(MODEL_NAME)


def get_client():
    """
    Creates a persistent ChromaDB client.
    """
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def build_vector_store() -> None:
    """
    Embeds all chunks and stores them in ChromaDB with metadata.
    """
    chunks = load_chunks()
    model = get_model()
    client = get_client()

    # Rebuild collection from scratch each time so old chunks do not remain.
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    ids = [chunk["id"] for chunk in chunks]
    documents = [chunk["text"] for chunk in chunks]
    metadatas = [chunk["metadata"] for chunk in chunks]

    print(f"Embedding {len(documents)} chunks with {MODEL_NAME}...")

    embeddings = model.encode(
        documents,
        normalize_embeddings=True,
        show_progress_bar=True,
    ).tolist()

    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings,
    )

    print(f"Saved {len(documents)} chunks to ChromaDB collection: {COLLECTION_NAME}")
    print(f"ChromaDB path: {CHROMA_DIR}")


def query_vector_store(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Searches ChromaDB and returns the top-k most relevant chunks.
    Lower cosine distance means a better match.
    """
    model = get_model()
    client = get_client()

    try:
        collection = client.get_collection(COLLECTION_NAME)
    except Exception as exc:
        raise RuntimeError(
            "Vector store not found. Run `python src/vector_store.py` first."
        ) from exc

    query_embedding = model.encode(
        [query],
        normalize_embeddings=True,
    ).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    retrieved = []

    for i in range(len(results["documents"][0])):
        retrieved.append(
            {
                "rank": i + 1,
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
            }
        )

    return retrieved


if __name__ == "__main__":
    build_vector_store()
