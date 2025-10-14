from beanie import Document
from datetime import datetime, timezone
from pydantic import Field
from typing import Literal

class Favorite(Document):
    user_id: str
    content_id: str
    name: str
    image: str
    content_type: Literal["movie", "series", "channel"]
    is_favorite: bool = True
    added_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "favourites"
