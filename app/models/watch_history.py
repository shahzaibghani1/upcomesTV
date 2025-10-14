from beanie import Document
from datetime import datetime, timezone
from pydantic import Field
from typing import Optional

class WatchHistory(Document):
    user_id: str
    content_id: str             # ID of movie/series/live_channel
    content_type: str           # "movie" | "series" | "live_channel"
    progress: Optional[float] = 0.0
    watched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "watch_history"
        collection = "watch_history"
