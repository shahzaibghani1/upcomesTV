from datetime import datetime, timezone
from beanie import Document
from pydantic import Field

class ContinueWatching(Document):
    user_id: str
    content_id: str
    progress: float = Field(default=0.0) 
    duration: float = Field(default=0.0) 
    last_watched: datetime = Field(default_factory=datetime.now(timezone.utc))

    class Settings:
        name = "continue_watching"
        collection = "continue_watching"

    class Config:
        schema_extra = {
            "example": {
                "user_id": "user123",
                "content_id": "movie456",
                "progress": 125.5,
                "duration": 3600.0,
                "last_watched": datetime.now(timezone.utc)
            }
        }