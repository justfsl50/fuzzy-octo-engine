"""Vector database abstraction layer."""


class VectorDB:
    def upsert(self, doc_id: str, embedding: list[float]) -> dict[str, str]:
        return {"doc_id": doc_id, "status": "stored", "dims": str(len(embedding))}
