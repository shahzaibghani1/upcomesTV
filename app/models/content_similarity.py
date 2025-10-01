from beanie import Document
from pydantic import Field
from typing import Optional


class ContentSimilarity(Document):
    content_id: str
    similar_content_id: str
    similarity_score: float = Field(0.0)

    class Settings:
        name = "content_similarity"
