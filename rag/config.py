"""Settings for the AI Lab, read from environment variables or a local .env file."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ollama_url: str = "http://localhost:11434"
    qdrant_url: str = "http://localhost:16335"
    ollama_model: str = "llama3.1:8b"
    embed_model: str = "nomic-embed-text"
    collection: str = "portfolio"

    # Cosine similarity of the best chunk below which a question counts as off-topic.
    # Tuned with evals/cases.yaml; see docs in CLAUDE.md and rag/answer.py.
    min_score: float = 0.58
    top_k: int = 5


settings = Settings()
