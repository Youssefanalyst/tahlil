from __future__ import annotations
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    # OpenRouter / LLM
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    openrouter_base_url: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    llm_model: str = os.getenv("LLM_MODEL", "minimax/minimax-m2:free")
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.1"))
    llm_timeout: int = int(os.getenv("LLM_TIMEOUT", "60"))

    # Embeddings + Vector store
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    index_path: str = os.getenv("INDEX_PATH", os.path.abspath(os.path.join(os.path.dirname(__file__), "store/faiss_index")))
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "1000"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "150"))
    k_retrieval: int = int(os.getenv("K_RETRIEVAL", "4"))


settings = Settings()

# Securely map OpenRouter to the OpenAI-compatible client used by LangChain
if settings.openrouter_api_key:
    # Many LangChain integrations read from OpenAI_* env vars
    os.environ.setdefault("OPENAI_API_KEY", settings.openrouter_api_key)
    os.environ.setdefault("OPENAI_API_BASE", settings.openrouter_base_url)
