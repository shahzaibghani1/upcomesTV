from fastapi import APIRouter, HTTPException, Body, Query
from typing import Literal, Optional, List
from bson import ObjectId
from pydantic import BaseModel
from app.models.favourite import Favorite
from app.models.movies import Movie
from app.models.series import Series
from app.models.live_channels import LiveChannel

router = APIRouter()

# --- 🚀 OPTIMIZATION: LIGHTWEIGHT PROJECTION MODELS ---
# ... (unchanged) ...
class MovieProjection(BaseModel):
    name: str
    stream_icon: Optional[str] = None
    stream_type: str = "movie"

class SeriesProjection(BaseModel):
    name: str
    cover: Optional[str] = None # Assuming 'cover' is the poster for series
    stream_type: str = "series"

class LiveChannelProjection(BaseModel):
    name: str
    stream_icon: Optional[str] = None
    stream_type: str = "live"
# --------------------------------------------------------


async def _get_content_details(content_id: str, content_type: str) -> Optional[dict]:
    """
    Get content details from the appropriate collection using Beanie projections.
    Fetches only minimal fields (name, poster, type) for the favorite list.
    NOTE: content_id is now expected to be the MongoDB ObjectId string.
    """
    try:
        # 1. Validate that the ID is a valid MongoDB ObjectId
        mongo_id = ObjectId(content_id)
    except Exception:
        print(f"DEBUG: Content ID '{content_id}' is NOT a valid ObjectId.")
        return None

    # 2. Use the ObjectId for finding the document (Movie.id is the Beanie representation of _id)
    # The crucial part is matching content_type to the correct collection lookup
    
    content = None
    print(f"DEBUG: Attempting lookup for ID: {content_id} in Collection: {content_type}")
    
    if content_type == "movie":
        # .id is the Beanie field corresponding to MongoDB's _id
        content = await Movie.find_one(Movie.id == mongo_id).project(MovieProjection)
    elif content_type == "series":
        content = await Series.find_one(Series.id == mongo_id).project(SeriesProjection)
    elif content_type == "live":
        content = await LiveChannel.find_one(LiveChannel.id == mongo_id).project(LiveChannelProjection)
    else:
        print(f"DEBUG: Invalid content_type received: {content_type}")
        return None

    if content:
        print("DEBUG: Content found successfully.")
        return content.model_dump()
    else:
        # This is where the 404 is being triggered if the content_type is wrong.
        print(f"DEBUG: Content NOT FOUND in the '{content_type}' collection.")
        return None


@router.put("/toggle", summary="Toggle Favorite Status")
async def toggle_favorite(
    user_id: str = Body(...),
    content_id: str = Body(...),
    content_type: Literal["movie", "series", "live"] = Body(...),
):
    """
    Toggle favorite status for a content item.
    """
    print(f"\n--- 🐛 DEBUG TOGGLE REQUEST START ---")
    print(f"User ID: {user_id}")
    print(f"Received Content ID: {content_id}")
    print(f"Received Content Type: {content_type}")
    print(f"--------------------------------------")
    
    # 1. Validate content exists using the MongoDB _id
    content_doc = await _get_content_details(content_id, content_type)
    
    if not content_doc:
        print("DEBUG: Content validation FAILED. Raising 404.")
        print(f"--- 🐛 DEBUG TOGGLE REQUEST END (404) ---\n")
        # This will now catch both invalid ObjectIds and content that doesn't exist
        raise HTTPException(status_code=404, detail="Content not found or Invalid Content ID")

    # 2. Check if favorite already exists using the MongoDB _id
    existing_fav = await Favorite.find_one(
        Favorite.user_id == user_id,
        Favorite.content_id == content_id # <-- content_id is the MongoDB _id
    )
    
    status = ""
    message = ""
    is_favorite = False
    favorite_id = None

    if existing_fav:
        # Delete existing favorite
        await existing_fav.delete()
        status = "removed"
        message = "Content removed from favorites"
        is_favorite = False
    else:
        # Create new favorite
        fav = Favorite(
            user_id=user_id,
            content_id=content_id, # <-- Save the MongoDB _id
            content_type=content_type
        )
        await fav.insert()
        status = "added"
        message = "Content added to favorites"
        is_favorite = True
        favorite_id = str(fav.id)
        
    print(f"DEBUG: Toggle successful. Status: {status}.")
    print(f"--- 🐛 DEBUG TOGGLE REQUEST END (200) ---\n")
    
    return {
        "status": status,
        "message": message,
        "favorite_id": favorite_id,
        "is_favorite": is_favorite
    }


@router.get("/{user_id}/content", summary="Get Favorite Content Details (Optimized)")
async def get_favorite_content(
    user_id: str,
    content_type: Optional[Literal["movie", "series", "live"]] = Query(None),
):
    """
    Get detailed content information for user's favorites, optimized to fetch 
    only name and poster for list display.
    """
    # Build query
    query = {"user_id": user_id}
    if content_type:
        query["content_type"] = content_type

    # Get user's favorites
    favorites = await Favorite.find(query).sort(-Favorite.added_at).to_list()
    
    content_details = []
    
    for fav in favorites:
        # Get complete content details (now uses the efficient Projection)
        # This will now use the MongoDB _id stored in fav.content_id
        content_data = await _get_content_details(fav.content_id, fav.content_type)
        
        if content_data:
            # We add back the favorite metadata here
            content_data.update({
                "favorite_id": str(fav.id),
                "content_id": fav.content_id,
                "added_at": fav.added_at.isoformat(),
                "is_favorite": True
            })
            content_details.append(content_data)
    
    return {
        "user_id": user_id,
        "content_type": content_type or "all",
        "count": len(content_details),
        "content": content_details
    }