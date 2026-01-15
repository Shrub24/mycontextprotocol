"""LLM-based document extraction for worker."""

from typing import Protocol, cast

import instructor
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from mycontextprotocol.config import Settings


class ExtractedFact(BaseModel):
    """A single extracted fact from content."""

    fact: str = Field(description="Concise factual statement")
    category: str = Field(description="Category: preference, skill, experience, goal, or fact")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0-1")


class ExtractedContent(BaseModel):
    """Structured extraction from document content."""

    summary: str = Field(description="Brief 1-2 sentence summary")
    facts: list[ExtractedFact] = Field(description="List of extracted facts")
    entities: list[str] = Field(description="Named entities (people, places, orgs, concepts)")
    topics: list[str] = Field(description="Main topics/themes")


class CompletionCreate(Protocol):
    async def __call__(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        response_model: type[ExtractedContent],
        max_retries: int,
    ) -> ExtractedContent: ...


class DocumentExtractor:
    def __init__(self, settings: Settings):
        self.settings = settings
        client = AsyncOpenAI(
            base_url=f"{settings.ollama_base_url}/v1",
            api_key="ollama",
        )
        self.instructor_client = instructor.patch(client)

    async def extract(self, content: str, user_id: str | None = None) -> ExtractedContent:
        """Extract structured information from document content.

        Args:
            content: Raw document text
            user_id: Optional user ID for user-specific extraction

        Returns:
            ExtractedContent with summary, facts, entities, topics
        """
        system_prompt = "Extract structured information from the provided content."
        if user_id:
            system_prompt += f" Focus on facts relevant to user {user_id}."

        create = cast("CompletionCreate", self.instructor_client.chat.completions.create)
        response = await create(
            model=self.settings.ollama_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content},
            ],
            response_model=ExtractedContent,
            max_retries=2,
        )

        return response
