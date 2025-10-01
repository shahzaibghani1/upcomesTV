from beanie import Document
from datetime import datetime, timezone
from pydantic import Field
from typing import Optional


class SearchHistory(Document):
    user_id: str 
    query: str
    search_type: str = "text"  
    created_at: datetime = Field(default_factory=datetime.now(timezone.utc))

    class Settings:
        name = "search_history"
