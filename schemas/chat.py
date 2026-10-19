from pydantic import BaseModel


class Chat(BaseModel):
    """Payload containing the user's natural language question for the AI agent."""
    query: str
