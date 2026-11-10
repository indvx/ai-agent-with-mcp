from pydantic import BaseModel, Field, field_validator


class Chat(BaseModel):
    """Payload containing the user's natural language question for the AI agent."""

    query: str = Field(..., min_length=1, max_length=4000, description="The user's question.")

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Query cannot be empty or whitespace only.")
        return stripped
