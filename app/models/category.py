# backend/app/models/category.py
from beanie import Document
from datetime import datetime, timezone
from pydantic import Field
from typing import Optional


class Category(Document):
    category_id: str            # e.g. "146"
    category_name: str          # e.g. "JUST RELEASED Hollywood"
    parent_id: int = 0          # e.g. 0

    # optional metadata (keeps the collection useful later)
    added: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "categories"
