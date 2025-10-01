# backend/app/models/watch_history.py
from beanie import Document
from datetime import datetime, timezone
from pydantic import Field
from typing import Optional

class WatchHistory(Document):
    user_id: str
    content_id: str  
    progress: Optional[int] = 0 
    watched_at: datetime = Field(default_factory=datetime.now(timezone.utc))

    class Settings:
        name = "watch_history"
