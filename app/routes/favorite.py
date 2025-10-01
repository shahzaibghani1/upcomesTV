from fastapi import APIRouter, HTTPException, Body, Query
from fastapi.encoders import jsonable_encoder
from typing import Literal

from app.models.favorite import Favorite
from app.models.content import Content

router = APIRouter(tags=["Favorites"])


# Add to favorites
@router.post("/", summary="Add to favorites")
async def add_to_favorites(
    user_id: str = Body(...),
    content_id: str = Body(...),
    category: Literal["movie", "series", "channel"] = Body(...)
):
    # Validate content exists
    content = await Content.get(content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    # Prevent duplicates
    existing = await Favorite.find_one({"user_id": user_id, "content_id": content_id})
    if existing:
        return {"status": "exists", "id": str(existing.id)}

    fav = Favorite(user_id=user_id, content_id=content_id, category=category)
    await fav.insert()
    return {"status": "added", "id": str(fav.id)}
    

# Get all favorites for a user (optionally by category)
@router.get("/{user_id}", summary="Get favorites")
async def get_favorites(user_id: str, category: str = Query(None)):
    query = {"user_id": user_id}
    if category:
        query["category"] = category

    favorites = await Favorite.find(query).sort(-Favorite.added_at).to_list()

    # Attach content info
    result = []
    for fav in favorites:
        content = await Content.get(fav.content_id)
        if content:
            result.append(
                {
                    "favorite_id": str(fav.id),
                    "category": fav.category,
                    "added_at": fav.added_at,
                    "content": jsonable_encoder(content),
                }
            )
    return {"favorites": result}


# Remove a single favorite
@router.delete("/{favorite_id}", summary="Remove from favorites")
async def remove_favorite(favorite_id: str):
    fav = await Favorite.get(favorite_id)
    if not fav:
        raise HTTPException(status_code=404, detail="Favorite not found")

    await fav.delete()
    return {"status": "removed", "id": favorite_id}
