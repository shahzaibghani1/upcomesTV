# backend/app/models/content.py
from beanie import Document
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import Field, BaseModel


class Episode(BaseModel):
    episode_num: int
    title: str
    stream_id: int
    stream_url: str


class Season(BaseModel):
    season_number: int
    episodes: List[Episode] = []


class Content(Document):
    tmdb_id: Optional[str] = None
    name: str
    content_type: str  # "movie" | "series" | "channel"
    stream_id: Optional[int] = Field(default=0)
    stream_url: Optional[str] = None  
    rating: Optional[float] = None
    genres: List[str] = Field(default_factory=list)
    cast: List[str] = Field(default_factory=list)
    director: Optional[str] = None
    category_id: Optional[str] = None  
    description: Optional[str] = None
    poster: Optional[str] = None     
    seasons: List[Season] = Field(default_factory=list) 
    last_updated: datetime = Field(default_factory=datetime.now(timezone.utc))

    class Settings:
        name = "content"
