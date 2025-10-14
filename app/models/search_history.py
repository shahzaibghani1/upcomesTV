# backend/app/models/search_history.py
from beanie import Document
from datetime import datetime
from pydantic import Field

class SearchHistory(Document):
    user_id: str
    query: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "search_history"  # MongoDB collection name
