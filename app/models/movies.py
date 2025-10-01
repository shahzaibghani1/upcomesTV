# backend/app/models/movie.py
from beanie import Document
from typing import Optional
from datetime import datetime, timezone
from pydantic import Field


class Movie(Document):
    tmdb_id: Optional[str] = None
    name: str
    stream_id: int
    stream_type: str = "movie"
    stream_icon: Optional[str] = None
    stream_url: Optional[str] = None
    rating: Optional[float] = None
    trailer: Optional[str] = None
    category_id: Optional[str] = None
    category_name: Optional[str] = None
    container_extension: Optional[str] = None
    is_adult: bool = False
    added: Optional[datetime] = None 
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "movies"
