from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from backend.config.loader import load_settings

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parents[2]

try:
    from qdrant_client import QdrantClient
    from qdrant_client import models as qmodels

    _QDRANT_AVAILABLE = True
except ImportError:
    _QDRANT_AVAILABLE = False


class RAGEngine:
    _instance: RAGEngine | None = None

    def __init__(self, config: dict[str, Any]) -> None:
        if not _QDRANT_AVAILABLE:
            raise RuntimeError(
                "RAGにはqdrant-client[fastembed]が必要です。"
                "pip install -e '.[rag]' でインストールしてください。"
            )
        self._config = config
        self._collection: str = config.get("collection", "personal_assistant")
        self._top_k: int = int(config.get("top_k", 5))
        self._client: QdrantClient | None = None
        self._initialized = False

    @classmethod
    def get_instance(cls) -> RAGEngine | None:
        if not _QDRANT_AVAILABLE:
            return None
        cfg = load_settings().get("rag", {})
        if not cfg.get("enabled", False):
            return None
        if cls._instance is None:
            cls._instance = cls(cfg)
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        cls._instance = None

    async def initialize(self) -> None:
        if self._initialized:
            return

        mode = self._config.get("mode", "local")
        if mode == "server":
            url = self._config.get("server_url", "http://localhost:6333")
            self._client = QdrantClient(url=url)
            logger.info("RAG: Qdrant server モード (%s)", url)
        else:
            local_path = _PROJECT_ROOT / self._config.get("local_path", "data/rag")
            local_path.mkdir(parents=True, exist_ok=True)
            self._client = QdrantClient(path=str(local_path))
            logger.info("RAG: Qdrant ローカルモード (%s)", local_path)

        model = self._config.get("embedding_model", "intfloat/multilingual-e5-small")
        self._client.set_model(model)

        existing = {c.name for c in self._client.get_collections().collections}
        if self._collection not in existing:
            self._client.create_collection(
                collection_name=self._collection,
                vectors_config=self._client.get_fastembed_vector_params(),
            )
            logger.info("RAG: コレクション '%s' を作成しました", self._collection)

        self._initialized = True

    def _point_id(self, doc_type: str, doc_id: str) -> int:
        h = hashlib.md5(f"{doc_type}:{doc_id}".encode()).hexdigest()
        return int(h[:8], 16)

    async def index_document(
        self,
        doc_type: str,
        doc_id: str,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if not self._initialized:
            await self.initialize()
        assert self._client is not None

        payload = {"type": doc_type, "doc_id": doc_id, **(metadata or {})}
        self._client.add(
            collection_name=self._collection,
            documents=[text],
            metadata=[payload],
            ids=[self._point_id(doc_type, doc_id)],
        )

    async def delete_document(self, doc_type: str, doc_id: str) -> None:
        if not self._initialized:
            await self.initialize()
        assert self._client is not None

        self._client.delete(
            collection_name=self._collection,
            points_selector=qmodels.PointIdsList(
                points=[self._point_id(doc_type, doc_id)]
            ),
        )

    async def search(self, query: str, limit: int | None = None) -> list[dict[str, Any]]:
        if not self._initialized:
            await self.initialize()
        assert self._client is not None

        results = self._client.query(
            collection_name=self._collection,
            query_text=query,
            limit=limit or self._top_k,
        )
        return [
            {
                "score": round(r.score, 4),
                "type": r.metadata.get("type", "unknown"),
                "doc_id": r.metadata.get("doc_id", ""),
                "text": r.document,
                **{k: v for k, v in r.metadata.items() if k not in ("type", "doc_id")},
            }
            for r in results
        ]
