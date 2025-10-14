# backend/app/models/series.py
from beanie import Document
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import Field, BaseModel


class Episode(BaseModel):
    episode_num: int
    title: str
    stream_id: int
    stream_url: str
    added: Optional[datetime] = None


class Season(BaseModel):
    season_number: int
    episodes: List[Episode] = Field(default_factory=list)


class Series(Document):
    series_id: int
    tmdb_id: Optional[str] = None  # Add this line
    name: str
    cover: Optional[str] = None
    plot: Optional[str] = None
    cast: List[str] = Field(default_factory=list)
    director: Optional[str] = None
    genre: List[str] = Field(default_factory=list)
    release_date: Optional[datetime] = None
    last_modified: Optional[datetime] = None
    rating: Optional[float] = None
    trailer: Optional[str] = None
    episode_run_time: Optional[int] = None
    category_id: Optional[str] = None
    category_name: Optional[str] = None
    stream_url: Optional[str] = None
    seasons: List[Season] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "series"
