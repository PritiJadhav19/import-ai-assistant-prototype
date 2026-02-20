from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Tuple
import hashlib
import re

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader

def _chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> List[str]:
    text = re.sub(r"\n{3,}", "\n\n", text.strip())
    chunks = []
    i = 0
    while i < len(text):
        chunks.append(text[i:i+chunk_size])
        i += max(1, chunk_size - overlap)
    return [c.strip() for c in chunks if c.strip()]

def _file_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:16]

@dataclass
class RetrievedChunk:
    text: str
    source: str
    page: int | None
    score: float

class ChromaRAG:
    """
    Persistent vector store (Chroma) + embeddings (sentence-transformers).
    Stores chunks with metadata: source filename, page number, chunk_id.
    """
    def __init__(self, persist_dir: str = "rag_db", collection_name: str = "import_docs"):
        self.persist_dir = persist_dir
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )
        self.col = self.client.get_or_create_collection(collection_name)
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

    def ingest_txt_bytes(self, data: bytes, filename: str):
        text = data.decode("utf-8", errors="ignore")
        self._ingest_text(text, filename, page=None, file_id=_file_hash(data))

    def ingest_pdf_bytes(self, data: bytes, filename: str):
        tmp = Path(self.persist_dir) / f"__tmp__{_file_hash(data)}.pdf"
        tmp.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_bytes(data)

        reader = PdfReader(str(tmp))
        for pno, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            if text.strip():
                self._ingest_text(text, filename, page=pno, file_id=_file_hash(data))

        try:
            tmp.unlink(missing_ok=True)
        except Exception:
            pass

    def _ingest_text(self, text: str, filename: str, page: int | None, file_id: str):
        chunks = _chunk_text(text)
        if not chunks:
            return

        ids = []
        metas: List[Dict[str, Any]] = []
        docs = []

        for idx, c in enumerate(chunks):
            chunk_id = f"{file_id}:{page or 0}:{idx}"
            ids.append(chunk_id)
            metas.append({"source": filename, "page": page, "chunk_index": idx})
            docs.append(c)

        # Remove duplicates if chunk_ids already exist
        # Chroma will error if same id exists; we can try delete then add
        try:
            self.col.delete(ids=ids)
        except Exception:
            pass

        embeddings = self.embedder.encode(docs).tolist()
        self.col.add(ids=ids, documents=docs, metadatas=metas, embeddings=embeddings)

    def search(self, query: str, k: int = 5) -> List[RetrievedChunk]:
        q_emb = self.embedder.encode([query]).tolist()
        res = self.col.query(query_embeddings=q_emb, n_results=k, include=["documents", "metadatas", "distances"])

        out: List[RetrievedChunk] = []
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        dists = res.get("distances", [[]])[0]

        # Chroma gives distance (lower is better). Convert to "score" where higher is better.
        for doc, meta, dist in zip(docs, metas, dists):
            score = float(1.0 / (1.0 + dist))
            out.append(RetrievedChunk(
                text=doc,
                source=meta.get("source", "unknown"),
                page=meta.get("page"),
                score=round(score, 4)
            ))
        return out