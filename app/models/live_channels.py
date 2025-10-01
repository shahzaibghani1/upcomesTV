# backend/app/models/live_channel.py
from beanie import Document
from typing import Optional, List
from datetime import datetime, timezone
from pydantic import Field


class LiveChannel(Document):
    stream_id: int
    name: str
    stream_type: str = "live"
    stream_icon: Optional[str] = None
    stream_url: Optional[str] = None
    epg_channel_id: Optional[str] = None
    category_id: Optional[str] = None
    category_name: Optional[str] = None 
    is_adult: bool = False
    tv_archive: Optional[int] = None
    tv_archive_duration: Optional[int] = None
    direct_source: Optional[str] = None
    added: Optional[datetime] = None  
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "live_channels"
