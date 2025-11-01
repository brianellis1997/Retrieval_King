import logging
from typing import List, Dict, Tuple
from sentence_transformers import CrossEncoder
from app.core import settings

logger = logging.getLogger(__name__)


class RerankerService:
    def __init__(self):
        self.model = None
        self._model_loaded = False
        self._load_attempted = False

    def _load_model(self):
        if self._load_attempted:
            return
        self._load_attempted = True
        logger.info(f"Loading reranker model: {settings.RERANKER_MODEL}")
        try:
            self.model = CrossEncoder(
                settings.RERANKER_MODEL,
                cache_folder=str(settings.MODELS_CACHE_DIR),
                device=settings.DEVICE if settings.DEVICE == "cuda" else "cpu"
            )
            self._model_loaded = True
            logger.info("Reranker model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load reranker model: {e}")
            self._model_loaded = False

    def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: int = None
    ) -> List[Tuple[int, float]]:
        try:
            if not self._model_loaded:
                self._load_model()

            if not self._model_loaded:
                raise RuntimeError("Reranker model failed to load. Reranking functionality is unavailable.")

            if top_k is None:
                top_k = settings.RERANK_TOP_K

            scores = self.model.predict([[query, doc] for doc in documents])

            ranked_indices = sorted(
                range(len(scores)),
                key=lambda i: scores[i],
                reverse=True
            )[:top_k]

            results = [(idx, float(scores[idx])) for idx in ranked_indices]

            logger.debug(f"Reranked {len(documents)} documents, returning top {len(results)}")
            return results

        except Exception as e:
            logger.error(f"Failed to rerank documents: {e}")
            raise

    def rerank_with_metadata(
        self,
        query: str,
        documents_with_metadata: List[Dict],
        top_k: int = None
    ) -> List[Tuple[Dict, float]]:
        try:
            if not self._model_loaded:
                self._load_model()

            if not self._model_loaded:
                raise RuntimeError("Reranker model failed to load. Reranking functionality is unavailable.")

            if top_k is None:
                top_k = settings.RERANK_TOP_K

            documents = [doc["text"] for doc in documents_with_metadata]
            scores = self.model.predict([[query, doc] for doc in documents])

            ranked_data = []
            for idx, score in enumerate(zip(range(len(scores)), scores)):
                doc_idx, doc_score = score
                ranked_data.append((documents_with_metadata[doc_idx], float(doc_score)))

            ranked_data.sort(key=lambda x: x[1], reverse=True)
            results = ranked_data[:top_k]

            logger.debug(f"Reranked {len(documents_with_metadata)} documents, returning top {len(results)}")
            return results

        except Exception as e:
            logger.error(f"Failed to rerank documents with metadata: {e}")
            raise


reranker_service = RerankerService()
