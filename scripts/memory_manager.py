from pathlib import Path
import chromadb
from scripts.ai_client import embed


class MemoryManager:
    def __init__(self, persona_id: int, chroma_path: str = None):
        self.persona_id = persona_id
        if chroma_path is None:
            chroma_path = str(Path(__file__).parent.parent / "data" / "chroma")
        self.client = chromadb.PersistentClient(path=chroma_path)
        self.collection = self.client.get_or_create_collection(
            name=f"persona_{persona_id}",
            metadata={"hnsw:space": "cosine"}
        )

    def add(self, source_type: str, text: str, metadata: dict) -> None:
        """Embed text and store in ChromaDB."""
        vector = embed(text)
        import hashlib, time
        doc_id = hashlib.md5(f"{text}{time.time()}".encode()).hexdigest()
        meta = {"source_type": source_type, **metadata}
        self.collection.add(
            ids=[doc_id],
            embeddings=[vector],
            documents=[text],
            metadatas=[meta]
        )

    def recall(self, query: str, top_k: int = 5) -> list[dict]:
        """Return top_k most relevant memory chunks for query."""
        vector = embed(query)
        count = self.count()
        if count == 0:
            return []
        results = self.collection.query(
            query_embeddings=[vector],
            n_results=min(top_k, count)
        )
        if not results["documents"][0]:
            return []
        return [
            {"text": doc, "metadata": meta}
            for doc, meta in zip(results["documents"][0], results["metadatas"][0])
        ]

    def count(self) -> int:
        return self.collection.count()

    def get_all(self) -> list[dict]:
        result = self.collection.get()
        return [
            {"id": id_, "text": doc, "metadata": meta}
            for id_, doc, meta in zip(result["ids"], result["documents"], result["metadatas"])
        ]

    def delete(self, doc_id: str) -> None:
        self.collection.delete(ids=[doc_id])
