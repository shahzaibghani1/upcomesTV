# backend/app/models/category.py
from beanie import Document
from datetime import datetime, timezone
from pydantic import Field
from typing import Optional


class Category(Document):
    category_id: str           
    category_name: str          
    parent_id: int = 0          
    added: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "categories"
