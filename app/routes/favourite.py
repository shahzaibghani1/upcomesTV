from fastapi import APIRouter, HTTPException, Body, Query
from typing import Literal, Optional
from bson import ObjectId
from app.models.favourite import Favorite
from app.models.movies import Movie
from app.models.series import Series
from app.models.live_channels import LiveChannel

router = APIRouter()

async def _get_content_details(content_id: str, content_type: str) -> Optional[dict]:
    """Get content details from the appropriate collection"""
    if not ObjectId.is_valid(content_id):
        return None

    if content_type == "movie":
        content = await Movie.get(content_id)
    elif content_type == "series":
        content = await Series.get(content_id)
    elif content_type == "channel":
        content = await LiveChannel.get(content_id)
    else:
        return None

    return content.model_dump() if content else None


@router.put("/toggle", summary="Toggle Favorite Status")
async def toggle_favorite(
    user_id: str = Body(...),
    content_id: str = Body(...),
    content_type: Literal["movie", "series", "channel"] = Body(...),
):
    """
    Toggle favorite status for a content item.
    - If favorite exists: delete it
    - If favorite doesn't exist: create it
    """
    # Validate content exists
    content_doc = await _get_content_details(content_id, content_type)
    if not content_doc:
        raise HTTPException(status_code=404, detail="Content not found")

    # Check if favorite already exists
    existing_fav = await Favorite.find_one(
        Favorite.user_id == user_id,
        Favorite.content_id == content_id
    )

    if existing_fav:
        # Delete existing favorite
        await existing_fav.delete()
        return {
            "status": "removed",
            "message": "Content removed from favorites",
            "is_favorite": False
        }
    else:
        # Create new favorite
        fav = Favorite(
            user_id=user_id,
            content_id=content_id,
            content_type=content_type
        )
        await fav.insert()
        return {
            "status": "added",
            "message": "Content added to favorites",
            "favorite_id": str(fav.id),
            "is_favorite": True
        }


@router.get("/{user_id}/content", summary="Get Favorite Content Details")
async def get_favorite_content(
    user_id: str,
    content_type: Optional[Literal["movie", "series", "channel"]] = Query(None),
):
    """
    Get detailed content information for user's favorites.
    Returns array of complete content details with joined data.
    """
    # Build query
    query = {"user_id": user_id}
    if content_type:
        query["content_type"] = content_type

    # Get user's favorites
    favorites = await Favorite.find(query).sort(-Favorite.added_at).to_list()
    
    content_details = []
    
    for fav in favorites:
        # Get complete content details
        content_data = await _get_content_details(fav.content_id, fav.content_type)
        
        if content_data:
            # Add favorite metadata to content data
            # content_data.update({
            #     "favorite_id": str(fav.id),
            #     "added_at": fav.added_at.isoformat(),
            #     "is_favorite": True
            # })
            content_details.append(content_data)
    
    return {
        "user_id": user_id,
        "content_type": content_type or "all",
        "count": len(content_details),
        "content": content_details
    }