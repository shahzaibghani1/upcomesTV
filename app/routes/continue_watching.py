# app/routes/continue_watching.py - CORRECTED
from fastapi import APIRouter, HTTPException
from app.models.continue_watching import ContinueWatching
from app.models.content import Content
from fastapi.encoders import jsonable_encoder
from datetime import datetime, timezone

router = APIRouter()

# Save or update progress
@router.post("/save")
async def save_progress(user_id: str, content_id: str, progress: float, duration: float):
    content = await Content.get(content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    # Movies / Series → remove if completed
    if content.content_type in ["movie", "series"]:
        if duration and progress / duration >= 0.9:
            # If it exists in continue_watching, remove it (since it's completed)
            doc = await ContinueWatching.find_one({"user_id": user_id, "content_id": content_id})
            if doc:
                await doc.delete()
            return {"status": "removed_from_continue", "reason": "completed"}

    # Channels → always keep in continue watching
    # Movies/Series (not completed) → save/update
    doc = await ContinueWatching.find_one({"user_id": user_id, "content_id": content_id})
    if doc:
        doc.progress = progress
        doc.duration = duration
        doc.last_watched = datetime.now(timezone.utc)
        await doc.save()
    else:
        doc = ContinueWatching(
            user_id=user_id,
            content_id=content_id,
            progress=progress,
            duration=duration
        )
        await doc.insert()

    return {"status": "saved", "id": str(doc.id)}

# Get all continue watching items for a user
@router.get("/{user_id}")
async def get_continue_watching(user_id: str):
    docs = await ContinueWatching.find({"user_id": user_id}).sort("-last_watched").to_list()
    results = []
    for d in docs:
        content = await Content.get(d.content_id)
        if content:
            content_data = jsonable_encoder(content)
            results.append({
                "content_id": d.content_id,
                "content": content_data,
                "stream_url": content.stream_url,
                "progress": d.progress,
                "duration": d.duration,
                "last_watched": d.last_watched,
            })
    return {"continue_watching": results}

# Remove one item (when user clicks "X")
@router.delete("/{user_id}/{content_id}")
async def clear_continue_watching(user_id: str, content_id: str):
    doc = await ContinueWatching.find_one({"user_id": user_id, "content_id": content_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    await doc.delete()
    return {"status": "removed", "content_id": content_id}