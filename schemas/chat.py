from typing import Optional
from pydantic import BaseModel, Field, field_validator


class Chat(BaseModel):
    """Payload containing the user's natural language question and session ID."""

    query: str = Field(..., min_length=1, max_length=4000, description="The user's question.")
    session_id: Optional[str] = Field(default=None, description="Conversation session identifier.")

    @field_validator("query")
    def validate_query(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Query cannot be empty or whitespace only.")
        return stripped
