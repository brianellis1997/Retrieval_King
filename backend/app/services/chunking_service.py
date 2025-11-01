import logging
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from transformers import AutoTokenizer
from app.core import settings

logger = logging.getLogger(__name__)


class ChunkingService:
    def __init__(self):
        self.chunk_size = settings.CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP
        self.tokenizer = None
        self._load_tokenizer()
        self.text_splitter = self._create_splitter()

    def _load_tokenizer(self):
        logger.info(f"Loading tokenizer for: {settings.EMBEDDING_MODEL}")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                settings.EMBEDDING_MODEL,
                cache_dir=str(settings.MODELS_CACHE_DIR)
            )
            logger.info("Tokenizer loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load tokenizer: {e}")
            raise

    def _create_splitter(self):
        def get_token_count(text: str) -> int:
            return len(self.tokenizer.encode(text))

        return RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", " ", ""],
            length_function=get_token_count,
            is_separator_regex=False
        )

    def chunk_text(self, text: str, document_id: str) -> List[dict]:
        try:
            chunks = self.text_splitter.split_text(text)

            chunked_data = []
            for idx, chunk in enumerate(chunks):
                token_count = len(self.tokenizer.encode(chunk))

                chunked_data.append({
                    "chunk_index": idx,
                    "document_id": document_id,
                    "text": chunk,
                    "token_count": token_count,
                    "page_number": None
                })

            logger.info(f"Chunked text into {len(chunked_data)} chunks, avg tokens: {sum(c['token_count'] for c in chunked_data) / len(chunked_data):.1f}")
            return chunked_data

        except Exception as e:
            logger.error(f"Failed to chunk text: {e}")
            raise

    def estimate_chunks(self, text: str) -> int:
        try:
            token_count = len(self.tokenizer.encode(text))
            estimated_chunks = max(1, (token_count + self.chunk_overlap) // (self.chunk_size - self.chunk_overlap))
            return estimated_chunks
        except Exception as e:
            logger.error(f"Failed to estimate chunks: {e}")
            return 1


chunking_service = ChunkingService()
