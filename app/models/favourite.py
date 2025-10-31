from beanie import Document
from datetime import datetime, timezone
from pydantic import Field
from typing import Literal

class Favorite(Document):
    user_id: str
    content_id: str
    content_type: Literal["movie", "series", "channel"]
    added_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "favourites"
        use_state_management = True

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "content_id": "movie_456", 
                "content_type": "movie",
                "added_at": "2024-01-15T10:30:00Z"
            }
        }