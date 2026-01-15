"""Central configuration for mycontextprotocol gateway and shared services."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    postgres_host: str = "postgresql-cluster-rw.database.svc.cluster.local"
    postgres_port: int = 5432
    postgres_user: str = "app"
    postgres_password: str

    dragonfly_host: str = "dragonfly.mycontextprotocol.svc.cluster.local"
    dragonfly_port: int = 6379
    dragonfly_password: str = ""

    ollama_base_url: str = "http://ollama.mycontextprotocol.svc.cluster.local:11434"
    ollama_model: str = "llama3.2"

    lightrag_host: str = "lightrag.lightrag.svc.cluster.local"
    lightrag_port: int = 9621
    lightrag_api_key: str = ""

    @property
    def postgres_connection_string(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/postgres"
