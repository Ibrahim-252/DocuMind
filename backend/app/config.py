from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore")

    database_url: str = "postgresql+psycopg://documind:documind@localhost:5432/documind"

    llm_provider: str = "anthropic"  # "anthropic" or "openrouter"
    llm_api_key: str = ""
    llm_model: str = "claude-sonnet-5-5"

    embedding_backend: str = "fastembed"  # "fastembed" or "fake"
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    similarity_threshold: float = 0.25

    upload_dir: str = "uploads"
    max_upload_mb: int = 20


settings = Settings()
