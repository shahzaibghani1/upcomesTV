# app/routes/continue_watching.py
from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder
from datetime import datetime, timezone
from app.models.continue_watching import ContinueWatching

# Import new content models
from app.models.movies import Movie
from app.models.series import Series
from app.models.live_channels import LiveChannel

router = APIRouter()


# 🟢 Helper function to fetch content dynamically
async def fetch_content(content_id: str, content_type: str):
    if content_type == "movie":
        return await Movie.get(content_id)
    elif content_type == "series":
        return await Series.get(content_id)
    elif content_type == "live_channel":
        return await LiveChannel.get(content_id)
    return None


# 🟢 Save or update progress
@router.post("/save")
async def save_progress(
    user_id: str,
    content_id: str,
    content_type: str,
    progress: float,
    duration: float
):
    # Fetch the content from correct collection
    content = await fetch_content(content_id, content_type)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    # For movies and series — remove if completed (>= 90%)
    if content_type in ["movie", "series"]:
        if duration and progress / duration >= 0.9:
            existing = await ContinueWatching.find_one({"user_id": user_id, "content_id": content_id})
            if existing:
                await existing.delete()
            return {"status": "removed_from_continue", "reason": "completed"}

    # Otherwise, save/update progress
    existing = await ContinueWatching.find_one({"user_id": user_id, "content_id": content_id})
    if existing:
        existing.progress = progress
        existing.duration = duration
        existing.last_watched = datetime.now(timezone.utc)
        await existing.save()
        doc_id = existing.id
    else:
        new_entry = ContinueWatching(
            user_id=user_id,
            content_id=content_id,
            content_type=content_type,
            progress=progress,
            duration=duration
        )
        await new_entry.insert()
        doc_id = new_entry.id

    return {"status": "saved", "id": str(doc_id)}


# 🟢 Get all continue watching items for a user
@router.get("/{user_id}")
async def get_continue_watching(user_id: str):
    docs = await ContinueWatching.find({"user_id": user_id}).sort("-last_watched").to_list()

    results = []
    for d in docs:
        content = await fetch_content(d.content_id, d.content_type)
        if content:
            results.append({
                "content_id": d.content_id,
                "content_type": d.content_type,
                "content": jsonable_encoder(content),
                "progress": d.progress,
                "duration": d.duration,
                "last_watched": d.last_watched,
            })

    return {"continue_watching": results}


# 🟢 Remove a single item (when user clicks "X")
@router.delete("/{user_id}/{content_id}")
async def remove_continue_watching(user_id: str, content_id: str):
    doc = await ContinueWatching.find_one({"user_id": user_id, "content_id": content_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Item not found")
    await doc.delete()
    return {"status": "removed", "content_id": content_id}
