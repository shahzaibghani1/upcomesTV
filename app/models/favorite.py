from beanie import Document
from datetime import datetime, timezone
from pydantic import Field
from typing import Literal

class Favorite(Document):
    user_id: str
    content_id: str  
    category: Literal["movie", "series", "channel"] 
    added_at: datetime = Field(default_factory=datetime.now(timezone.utc))

    class Settings:
        name = "favorites"
