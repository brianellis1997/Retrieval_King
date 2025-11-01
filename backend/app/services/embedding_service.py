import logging
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer
from app.core import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self):
        self.model = None
        self._load_model()

    def _load_model(self):
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
        try:
            self.model = SentenceTransformer(
                settings.EMBEDDING_MODEL,
                cache_folder=str(settings.MODELS_CACHE_DIR),
                device=settings.DEVICE if settings.DEVICE == "cuda" else "cpu"
            )
            logger.info(f"Embedding model loaded successfully")
            logger.info(f"Model dimension: {self.model.get_sentence_embedding_dimension()}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        try:
            embeddings = self.model.encode(
                texts,
                batch_size=32,
                show_progress_bar=True,
                convert_to_numpy=True
            )
            logger.debug(f"Embedded {len(texts)} texts, shape: {embeddings.shape}")
            return embeddings
        except Exception as e:
            logger.error(f"Failed to embed texts: {e}")
            raise

    def embed_query(self, query: str) -> np.ndarray:
        try:
            embedding = self.model.encode(
                query,
                convert_to_numpy=True
            )
            logger.debug(f"Embedded query, shape: {embedding.shape}")
            return embedding
        except Exception as e:
            logger.error(f"Failed to embed query: {e}")
            raise

    def get_embedding_dimension(self) -> int:
        return self.model.get_sentence_embedding_dimension()


embedding_service = EmbeddingService()
