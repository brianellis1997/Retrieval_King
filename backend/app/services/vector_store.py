import logging
from typing import List, Dict, Tuple
import chromadb
from app.core import settings

logger = logging.getLogger(__name__)


class VectorStoreService:
    def __init__(self):
        self.client = None
        self.collection = None
        self._initialize_db()

    def _initialize_db(self):
        logger.info(f"Initializing ChromaDB at {settings.DATABASE_PATH}")
        try:
            self.client = chromadb.PersistentClient(
                path=str(settings.DATABASE_PATH)
            )

            self.collection = self.client.get_or_create_collection(
                name="documents",
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("ChromaDB initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise

    def add_documents(
        self,
        chunk_texts: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict],
        ids: List[str]
    ) -> bool:
        try:
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=chunk_texts
            )
            logger.info(f"Added {len(ids)} documents to vector store")
            return True
        except Exception as e:
            logger.error(f"Failed to add documents to vector store: {e}")
            raise

    def search(
        self,
        query_embedding: List[float],
        top_k: int = None
    ) -> List[Dict]:
        try:
            if top_k is None:
                top_k = settings.RETRIEVAL_TOP_K

            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )

            retrieved_docs = []
            if results and results["documents"]:
                for i, (doc, metadata, distance) in enumerate(
                    zip(
                        results["documents"][0],
                        results["metadatas"][0],
                        results["distances"][0]
                    )
                ):
                    similarity_score = 1 - distance
                    retrieved_docs.append({
                        "text": doc,
                        "metadata": metadata,
                        "similarity_score": similarity_score,
                        "rank": i + 1
                    })

            logger.debug(f"Retrieved {len(retrieved_docs)} documents from vector store")
            return retrieved_docs

        except Exception as e:
            logger.error(f"Failed to search vector store: {e}")
            raise

    def delete_document(self, document_id: str) -> bool:
        try:
            where_filter = {"document_id": {"$eq": document_id}}
            self.collection.delete(where=where_filter)
            logger.info(f"Deleted document {document_id} from vector store")
            return True
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            raise

    def get_collection_stats(self) -> Dict:
        try:
            count = self.collection.count()
            return {
                "total_chunks": count,
                "collection_name": self.collection.name
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {"error": str(e)}

    def clear_collection(self) -> bool:
        try:
            self.client.delete_collection(name="documents")
            self.collection = self.client.get_or_create_collection(
                name="documents",
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("Cleared vector store")
            return True
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
            raise


vector_store_service = VectorStoreService()
