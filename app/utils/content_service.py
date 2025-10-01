from typing import List, Dict, Any
from datetime import datetime, timezone
import random
from app.models.content import Content
from app.models.content_similarity import ContentSimilarity


# -------------------------------
# MOCK fetchers (replace with real IPTV/TMDB calls later)
# -------------------------------
def fetch_mock_movies() -> List[Dict[str, Any]]:
    """Return a list of mock movie dicts similar to what IPTV/TMDB would return."""
    sample = [
        {
            "tmdb_id": "tmdb_101",
            "name": "The Mock Avenger",
            "content_type": "movie",
            "stream_id": 101,
            "rating": 7.8,
            "genres": ["Action", "Adventure"],
            "cast": ["Actor A", "Actor B"],
            "director": "Director X",
            "category_id": "cat_action",
            "description": "An action-packed mock movie.",
            "poster": "https://example.com/posters/101.jpg"
        },
        {
            "tmdb_id": "tmdb_102",
            "name": "Mock Drama",
            "content_type": "movie",
            "stream_id": 102,
            "rating": 6.4,
            "genres": ["Drama"],
            "cast": ["Actor C"],
            "director": "Director Y",
            "category_id": "cat_drama",
            "description": "A mock drama film.",
            "poster": "https://example.com/posters/102.jpg"
        }
    ]
    return sample


def fetch_mock_series() -> List[Dict[str, Any]]:
    sample = [
        {
            "tmdb_id": "tmdb_s201",
            "name": "Mock Series One",
            "content_type": "series",
            "stream_id": 201,
            "rating": 8.1,
            "genres": ["Drama", "Mystery"],
            "cast": ["Actor D"],
            "director": "Director Z",
            "category_id": "cat_series",
            "description": "A mysterious mock series.",
            "poster": "https://example.com/posters/s201.jpg"
        }
    ]
    return sample


def fetch_mock_channels() -> List[Dict[str, Any]]:
    sample = [
        {
            "tmdb_id": None,
            "name": "Mock Channel 24",
            "content_type": "channel",
            "stream_id": 3001,
            "rating": None,
            "genres": ["News"],
            "cast": [],
            "director": None,
            "category_id": "cat_channel",
            "description": "A 24/7 mock news channel.",
            "poster": None
        }
    ]
    return sample


# -------------------------------
# Sync logic
# -------------------------------
async def sync_content_from_mock():
    """
    Fetch mock content and upsert into Content collection.
    Returns number of inserted/updated items.
    """
    inserted = 0
    updated = 0

    movies = fetch_mock_movies()
    series = fetch_mock_series()
    channels = fetch_mock_channels()

    all_items = movies + series + channels

    for item in all_items:
        stream_id = item.get("stream_id") or 0

        # try to find existing by stream_id (same logic as your Django migration changes)
        existing = await Content.find_one(Content.stream_id == stream_id)

        if existing:
            # update fields
            existing.tmdb_id = item.get("tmdb_id")
            existing.name = item.get("name", existing.name)
            existing.content_type = item.get("content_type", existing.content_type)
            existing.rating = item.get("rating")
            existing.genres = item.get("genres", [])
            existing.cast = item.get("cast", [])
            existing.director = item.get("director")
            existing.category_id = item.get("category_id")
            existing.description = item.get("description")
            existing.poster = item.get("poster")
            existing.last_updated = datetime.now(timezone.utc)
            await existing.save()
            updated += 1
        else:
            doc = Content(
                tmdb_id=item.get("tmdb_id"),
                name=item.get("name", ""),
                content_type=item.get("content_type", "movie"),
                stream_id=stream_id,
                rating=item.get("rating"),
                genres=item.get("genres", []),
                cast=item.get("cast", []),
                director=item.get("director"),
                category_id=item.get("category_id"),
                description=item.get("description"),
                poster=item.get("poster"),
                last_updated=datetime.now(timezone.utc)
            )
            await doc.insert()
            inserted += 1

    # Optionally: create some dummy similarities for demo (not real TF-IDF)
    # Clear old (for demo)
    await ContentSimilarity.find_all().delete()
    contents = await Content.find_all().to_list()
    if len(contents) >= 2:
        # create random similarity relations for demo
        for i in range(min(50, len(contents))):
            c1 = random.choice(contents)
            c2 = random.choice(contents)
            if c1.id != c2.id:
                sim = ContentSimilarity(
                    content_id=str(c1.id),
                    similar_content_id=str(c2.id),
                    similarity_score=round(random.uniform(0.2, 0.95), 3)
                )
                await sim.insert()

    return {"inserted": inserted, "updated": updated}
