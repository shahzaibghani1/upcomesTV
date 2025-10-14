from datetime import datetime, timezone
from beanie import Document
from pydantic import Field
from typing import Optional

class ContinueWatching(Document):
    user_id: str
    content_id: str
    content_type: str           # "movie" | "series" | "live_channel"
    progress: Optional[float] = 0.0   # seconds or percentage watched
    duration: Optional[float] = 0.0   # total seconds if available
    last_watched: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "continue_watching"
        collection = "continue_watching"
