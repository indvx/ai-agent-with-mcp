from typing import Optional
from pydantic import BaseModel, Field


class UpdateDatabase(BaseModel):
    """Payload for updating database status and default flags."""

    is_default: Optional[bool] = Field(
        default=None,
        description="Whether this database is the predefined fallback default",
    )
    status: Optional[int] = Field(
        default=None,
        description="Database active status (1 for active, 0 for inactive)",
    )
