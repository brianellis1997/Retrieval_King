import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_TITLE: str = "Retrieval King"
    API_VERSION: str = "0.1.0"

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL_QUERY_REWRITER: str = "gpt-4o-mini"
    OPENAI_MODEL_GENERATOR: str = "gpt-4o-mini"

    DATABASE_PATH: Path = Path("./data/chroma")
    UPLOADS_DIR: Path = Path("./data/uploads")
    MODELS_CACHE_DIR: Path = Path("./data/models")

    EMBEDDING_MODEL: str = "ibm-granite/granite-embedding-30m-english"
    RERANKER_MODEL: str = "ibm-granite/granite-embedding-reranker-english-r2"
    OCR_MODEL: str = "deepseek-ai/DeepSeek-OCR"

    CHUNK_SIZE: int = 450
    CHUNK_OVERLAP: int = 75
    RETRIEVAL_TOP_K: int = 100
    RERANK_TOP_K: int = 10

    DEVICE: str = "cuda"

    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    def __init__(self, **data):
        super().__init__(**data)
        self.DATABASE_PATH.mkdir(parents=True, exist_ok=True)
        self.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        self.MODELS_CACHE_DIR.mkdir(parents=True, exist_ok=True)


settings = Settings()
