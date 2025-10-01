# backend/app/routes/watch_history.py
from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional
from fastapi.encoders import jsonable_encoder
from datetime import datetime, timezone

from app.models.watch_history import WatchHistory
from app.models.content import Content

router = APIRouter()


# Add to watch history (only if completed or channel)
@router.post("/", summary="Record watch history (prevent duplicates)")
async def add_watch_history(
    user_id: str = Body(...),
    content_id: str = Body(...),
    progress: float = Body(...),
    duration: Optional[float] = Body(None),
):
    # Validate content exists
    content = await Content.get(content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    is_completed = False

    # Movies / Series → add only if watched >= 90%
    if content.content_type in ["movie", "series"] and duration:
        if progress / duration >= 0.9:
            is_completed = True

    # Channels → always add to history
    if content.content_type == "channel":
        is_completed = True

    if not is_completed:
        return {"status": "skipped", "reason": "not completed"}

    # Check if this content is already in the user's history
    existing = await WatchHistory.find_one({"user_id": user_id, "content_id": content_id})
    if existing:
        existing.progress = progress
        existing.watched_at = datetime.now(timezone.utc)
        await existing.save()
        return {"status": "updated", "id": str(existing.id)}

    # Otherwise, insert a new history entry
    history = WatchHistory(user_id=user_id, content_id=content_id, progress=progress)
    await history.insert()
    return {"status": "added", "id": str(history.id)}


# Get user watch history (deduplicated per content, latest only)
@router.get("/{user_id}", summary="Get watch history for a user")
async def get_watch_history(user_id: str, limit: int = Query(20, ge=1)):
    histories = (
        await WatchHistory.find({"user_id": user_id})
        .sort(-WatchHistory.watched_at)
        .to_list()
    )

    # Deduplicate: only keep the latest entry per content_id
    latest_by_content = {}
    for h in histories:
        if h.content_id not in latest_by_content:
            latest_by_content[h.content_id] = h  # first occurrence is the latest due to sort

    # Apply limit after deduplication
    limited_histories = list(latest_by_content.values())[:limit]

    # Attach content info
    result = []
    for h in limited_histories:
        content = await Content.get(h.content_id)
        if content:
            result.append(
                {
                    "history_id": str(h.id),
                    "watched_at": h.watched_at,
                    "progress": h.progress,
                    "content": jsonable_encoder(content),
                }
            )
    return {"history": result}


# Delete an entry
@router.delete("/{history_id}", summary="Remove an item from watch history")
async def delete_watch_history(history_id: str):
    history = await WatchHistory.get(history_id)
    if not history:
        raise HTTPException(status_code=404, detail="History not found")

    await history.delete()
    return {"status": "deleted", "id": history_id}


# Clear all watch history for a user
@router.delete("/clear/{user_id}", summary="Clear all watch history for a user")
async def clear_watch_history(user_id: str):
    deleted = await WatchHistory.find({"user_id": user_id}).delete()
    return {"status": "cleared", "user_id": user_id, "deleted_count": deleted.deleted_count}
