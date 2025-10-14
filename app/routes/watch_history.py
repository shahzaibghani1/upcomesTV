# backend/app/routes/watch_history.py
from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional
from fastapi.encoders import jsonable_encoder
from datetime import datetime, timezone

from app.models.watch_history import WatchHistory
from app.models.movies import Movie
from app.models.series import Series
from app.models.live_channels import LiveChannel

router = APIRouter()

# =========================
# ADD TO WATCH HISTORY
# =========================
@router.post("/", summary="Record watch history (prevent duplicates)")
async def add_watch_history(
    user_id: str = Body(...),
    content_id: str = Body(...),
    content_type: str = Body(..., description="movie | series | live_channel"),
    progress: float = Body(...),
    duration: Optional[float] = Body(None),
):
    # ✅ Validate that content exists in the appropriate collection
    content = None
    if content_type == "movie":
        content = await Movie.get(content_id)
    elif content_type == "series":
        content = await Series.get(content_id)
    elif content_type == "live_channel":
        content = await LiveChannel.get(content_id)
    else:
        raise HTTPException(status_code=400, detail="Invalid content type")

    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    # ✅ Check completion logic
    is_completed = False
    if content_type in ["movie", "series"] and duration:
        if progress / duration >= 0.9:
            is_completed = True
    elif content_type == "live_channel":
        is_completed = True

    if not is_completed:
        return {"status": "skipped", "reason": "not completed"}

    # ✅ Check if already exists — update progress/time
    existing = await WatchHistory.find_one({"user_id": user_id, "content_id": content_id})
    if existing:
        existing.progress = progress
        existing.watched_at = datetime.now(timezone.utc)
        await existing.save()
        return {"status": "updated", "id": str(existing.id)}

    # ✅ Create a new record
    history = WatchHistory(
        user_id=user_id,
        content_id=content_id,
        content_type=content_type,
        progress=progress,
    )
    await history.insert()
    return {"status": "added", "id": str(history.id)}


# =========================
# GET WATCH HISTORY
# =========================
@router.get("/{user_id}", summary="Get watch history for a user")
async def get_watch_history(user_id: str, limit: int = Query(20, ge=1)):
    histories = (
        await WatchHistory.find({"user_id": user_id})
        .sort(-WatchHistory.watched_at)
        .to_list()
    )

    # Deduplicate per content_id (latest only)
    latest_by_content = {}
    for h in histories:
        if h.content_id not in latest_by_content:
            latest_by_content[h.content_id] = h

    limited_histories = list(latest_by_content.values())[:limit]

    # ✅ Attach content details based on content_type
    result = []
    for h in limited_histories:
        content = None
        if h.content_type == "movie":
            content = await Movie.get(h.content_id)
        elif h.content_type == "series":
            content = await Series.get(h.content_id)
        elif h.content_type == "live_channel":
            content = await LiveChannel.get(h.content_id)

        if content:
            result.append(
                {
                    "history_id": str(h.id),
                    "watched_at": h.watched_at,
                    "progress": h.progress,
                    "content_type": h.content_type,
                    "content": {
                        "_id": str(content.id),
                        "name": getattr(content, "name", None),
                        "stream_icon": getattr(content, "stream_icon", None)
                        or getattr(content, "cover", None),
                    },
                }
            )

    return {"history": result}


# =========================
# DELETE SINGLE ENTRY
# =========================
@router.delete("/{history_id}", summary="Remove an item from watch history")
async def delete_watch_history(history_id: str):
    history = await WatchHistory.get(history_id)
    if not history:
        raise HTTPException(status_code=404, detail="History not found")

    await history.delete()
    return {"status": "deleted", "id": history_id}


# =========================
# CLEAR ALL HISTORY
# =========================
@router.delete("/clear/{user_id}", summary="Clear all watch history for a user")
async def clear_watch_history(user_id: str):
    deleted = await WatchHistory.find({"user_id": user_id}).delete()
    return {"status": "cleared", "user_id": user_id, "deleted_count": deleted.deleted_count}
