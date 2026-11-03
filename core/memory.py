"""
Dual-tier memory system: Short-term conversation history and Long-term episodic memory.
"""
from typing import Any, Dict, List, Optional
import math
import re


class Message:
    def __init__(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        self.role = role
        self.content = content
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {"role": self.role, "content": self.content, "metadata": self.metadata}


class ShortTermMemory:
    """Sliding-window short term buffer with token awareness."""

    def __init__(self, max_messages: int = 20):
        self.max_messages = max_messages
        self.messages: List[Message] = []

    def add(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        self.messages.append(Message(role=role, content=content, metadata=metadata))
        if len(self.messages) > self.max_messages:
            # Preserve system prompt if present at index 0
            if self.messages[0].role == "system":
                self.messages = [self.messages[0]] + self.messages[-(self.max_messages - 1):]
            else:
                self.messages = self.messages[-self.max_messages:]

    def get_context(self) -> List[Dict[str, Any]]:
        return [m.to_dict() for m in self.messages]

    def clear(self) -> None:
        self.messages.clear()


class LongTermMemory:
    """Episodic memory store with lightweight TF-IDF semantic similarity retrieval."""

    def __init__(self):
        self.documents: List[Dict[str, Any]] = []

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"\w+", text.lower())

    def add_document(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        tokens = self._tokenize(text)
        tf: Dict[str, float] = {}
        for t in tokens:
            tf[t] = tf.get(t, 0.0) + 1.0
        # Normalize TF
        total = len(tokens) or 1
        for t in tf:
            tf[t] /= total

        self.documents.append({
            "text": text,
            "tf": tf,
            "metadata": metadata or {},
        })

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        query_tokens = self._tokenize(query)
        if not query_tokens or not self.documents:
            return []

        # Compute document frequency
        df: Dict[str, int] = {}
        n_docs = len(self.documents)
        for doc in self.documents:
            seen = set(doc["tf"].keys())
            for token in query_tokens:
                if token in seen:
                    df[token] = df.get(token, 0) + 1

        # Score documents via Cosine-like TF-IDF
        scored = []
        for doc in self.documents:
            score = 0.0
            for token in query_tokens:
                if token in doc["tf"]:
                    idf = math.log((n_docs + 1) / (df.get(token, 0) + 1)) + 1.0
                    score += doc["tf"][token] * idf
            if score > 0:
                scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {"score": round(item[0], 4), "text": item[1]["text"], "metadata": item[1]["metadata"]}
            for item in scored[:top_k]
        ]
