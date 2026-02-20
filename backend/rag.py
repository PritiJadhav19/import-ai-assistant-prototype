from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple
import re

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer


def chunk_text(text: str, chunk_size: int = 600, overlap: int = 80) -> List[str]:
    text = re.sub(r"\n{3,}", "\n\n", text.strip())
    chunks = []
    i = 0
    while i < len(text):
        chunks.append(text[i : i + chunk_size])
        i += max(1, chunk_size - overlap)
    return [c.strip() for c in chunks if c.strip()]


@dataclass
class DocChunk:
    source: str
    text: str


class SimpleRAG:
    def __init__(self):
        self.chunks: List[DocChunk] = []
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.matrix = None

    def ingest_text(self, text: str, source: str):
        for c in chunk_text(text):
            self.chunks.append(DocChunk(source=source, text=c))
        self._rebuild_index()

    def ingest_file(self, path: Path):
        text = path.read_text(encoding="utf-8", errors="ignore")
        self.ingest_text(text, source=path.name)

    def _rebuild_index(self):
        corpus = [c.text for c in self.chunks]
        if not corpus:
            self.matrix = None
            return
        self.matrix = self.vectorizer.fit_transform(corpus)

    def search(self, query: str, k: int = 4) -> List[Tuple[DocChunk, float]]:
        if not self.chunks or self.matrix is None:
            return []
        qv = self.vectorizer.transform([query])
        scores = (self.matrix @ qv.T).toarray().ravel()
        idx = np.argsort(-scores)[:k]
        results = [(self.chunks[i], float(scores[i])) for i in idx if scores[i] > 0.0]
        return results