# app/routes/favourites.py
from fastapi import APIRouter, HTTPException, Body, Query
from typing import Literal, Optional
from bson import ObjectId
from fastapi.encoders import jsonable_encoder
from app.models.favourite import Favorite
from app.db import movies_collection, series_collection, channels_collection

router = APIRouter()

async def _get_content_doc(content_id: str, content_type: str) -> Optional[dict]:

    if not ObjectId.is_valid(content_id):
        return None

    oid = ObjectId(content_id)

    if content_type == "movie":
        doc = await movies_collection.find_one({"_id": oid})
    elif content_type == "series":
        doc = await series_collection.find_one({"_id": oid})
    elif content_type == "channel":
        doc = await channels_collection.find_one({"_id": oid})
    else:
        doc = None

    return doc


# Add to favorites
@router.post("/", summary="Add to favorites")
async def add_to_favorites(
    user_id: str = Body(...),
    content_id: str = Body(...),
    content_type: Literal["movie", "series", "channel"] = Body(...),
):
    # Validate content exists in the corresponding collection
    content_doc = await _get_content_doc(content_id, content_type)
    if content_doc is None:
        raise HTTPException(status_code=404, detail="Content not found")

    # Prevent duplicates
    existing = await Favorite.find_one({"user_id": user_id, "content_id": content_id})
    if existing:
        return {"status": "exists", "id": str(existing.id)}

    # Determine image field depending on content_type
    image_val = ""
    if content_type == "movie" or content_type == "channel":
        image_val = content_doc.get("stream_icon") or ""
    elif content_type == "series":
        image_val = content_doc.get("cover") or ""

    fav = Favorite(
        user_id=user_id,
        content_id=content_id,
        name=content_doc.get("name", ""),
        image=image_val,
        content_type=content_type,
        is_favorite=True,
    )

    await fav.insert()
    return {"status": "added", "id": str(fav.id)}


# Get all favorites for a user (optionally filtered by content_type)
@router.get("/{user_id}", summary="Get favorites")
async def get_favorites(
    user_id: str,
    content_type: Optional[Literal["movie", "series", "channel"]] = Query(None),
):
    query = {"user_id": user_id}
    if content_type:
        query["content_type"] = content_type

    favorites = await Favorite.find(query).sort(-Favorite.added_at).to_list()

    result = []
    for fav in favorites:
        # Use stored name/image in favorite document as source of truth,
        # but attempt to fetch the latest content doc to override if available
        content_doc = await _get_content_doc(fav.content_id, fav.content_type)
        if content_doc:
            if fav.content_type in ("movie", "channel"):
                image = content_doc.get("stream_icon") or fav.image or ""
            else:
                image = content_doc.get("cover") or fav.image or ""
            name = content_doc.get("name") or fav.name or ""
        else:
            # content missing from main collections (deleted or removed) -> fallback to fav fields
            image = fav.image or ""
            name = fav.name or ""

        result.append(
            {
                "favorite_id": str(fav.id),
                "content_id": fav.content_id,
                "_id": fav.content_id,
                "name": name,
                "image": image,
                "type": fav.content_type,
                "is_favorite": fav.is_favorite,
                "added_at": fav.added_at.isoformat() if hasattr(fav, "added_at") else None,
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
