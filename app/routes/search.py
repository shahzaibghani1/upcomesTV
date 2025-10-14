# backend/app/routes/search.py
from fastapi import APIRouter, Query, HTTPException
from fastapi.encoders import jsonable_encoder
from typing import List
from app.models.search_history import SearchHistory
from app.models.movies import Movie
from app.models.series import Series
from app.models.live_channels import LiveChannel

router = APIRouter()

# ========== SEARCH CONTENT (Movies + Series + Live Channels) ==========
@router.get("", summary="Search across movies, series, and live channels")
async def search_content(
    q: str = Query(..., description="Search query string"),
    user_id: str = Query(..., description="User performing search"),
    limit: int = Query(100, ge=1, le=200, description="Max number of search results to return"),
):
    if not q.strip():
        raise HTTPException(status_code=400, detail="Query string cannot be empty")

    # ✅ Save in search history
    history = SearchHistory(user_id=user_id, query=q)
    await history.insert()

    regex_query = {"$regex": q, "$options": "i"}

    # ✅ Perform searches
    movie_results = await Movie.find({"name": regex_query}).limit(limit).to_list()
    series_results = await Series.find({"name": regex_query}).limit(limit).to_list()
    live_results = await LiveChannel.find({"name": regex_query}).limit(limit).to_list()

    all_results = []

    for m in movie_results:
        all_results.append({
            "_id": str(m.id),
            "name": m.name,
            "stream_icon": m.stream_icon,
            "type": "movie",
            "is_favourite": False,
        })

    for s in series_results:
        all_results.append({
            "_id": str(s.id),
            "name": s.name,
            "stream_icon": s.cover,
            "type": "series",
            "is_favourite": False,
        })

    for l in live_results:
        all_results.append({
            "_id": str(l.id),
            "name": l.name,
            "stream_icon": l.stream_icon,
            "type": "live_channel",
            "is_favourite": False,
        })

    all_results.sort(key=lambda x: x["name"].lower())
    all_results = all_results[:limit]

    return {
        "total": len(all_results),
        "limit": limit,
        "items": all_results,
    }


# ========== SEARCH HISTORY ==========

@router.get("/history", summary="Get search history for a user")
async def get_search_history(user_id: str = Query(...)):
    history = await SearchHistory.find(
        SearchHistory.user_id == user_id
    ).sort(-SearchHistory.created_at).to_list()
    return {"history": [jsonable_encoder(h) for h in history]}


@router.delete("/history/all/clear", summary="Clear all search history for a user")
async def clear_search_history(user_id: str = Query(...)):
    await SearchHistory.find(SearchHistory.user_id == user_id).delete()
    return {"status": "cleared", "user_id": user_id}


@router.delete("/history/{history_id}", summary="Delete one history entry")
async def delete_search_history(history_id: str, user_id: str = Query(...)):
    history = await SearchHistory.get(history_id)
    if not history:
        raise HTTPException(status_code=404, detail="History entry not found")

    if history.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this entry")

    await history.delete()
    return {"status": "deleted", "id": history_id}
