from fastapi import APIRouter, Query, HTTPException, Depends
from fastapi.encoders import jsonable_encoder
from typing import Optional
from app.models.content import Content
from app.models.search_history import SearchHistory

router = APIRouter(tags=["search"])


# ========== SEARCH CONTENT ==========
@router.get("/search", summary="Search content by name, genre, or cast")
async def search_content(
    q: str = Query(..., description="Search query string"),
    user_id: str = Query(..., description="User performing search"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    if not q.strip():
        raise HTTPException(status_code=400, detail="Query string cannot be empty")

    # Determine type (just a rough guess, frontend may decide too)
    search_type = "text"
    if q.lower() in ["action", "drama", "comedy"]:  # simplistic genre detection
        search_type = "genre"

    # Save in search history (always)
    history = SearchHistory(user_id=user_id, query=q, search_type=search_type)
    await history.insert()

    # Query DB
    query = {
        "$or": [
            {"name": {"$regex": q, "$options": "i"}},
            {"genres": {"$regex": q, "$options": "i"}},
            {"cast": {"$regex": q, "$options": "i"}}
        ]
    }

    skip = (page - 1) * page_size
    total = await Content.find(query).count()
    items = await Content.find(query).skip(skip).limit(page_size).to_list()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [jsonable_encoder(i) for i in items],
    }


# ========== HISTORY ==========
@router.get("/search/history", summary="Get search history for a user")
async def get_search_history(user_id: str = Query(...)):
    history = await SearchHistory.find(SearchHistory.user_id == user_id).sort(
        -SearchHistory.created_at
    ).to_list()
    return {"history": [jsonable_encoder(h) for h in history]}


@router.delete("/search/history/{history_id}", summary="Delete one history entry")
async def delete_search_history(history_id: str):
    history = await SearchHistory.get(history_id)
    if not history:
        raise HTTPException(status_code=404, detail="History entry not found")
    await history.delete()
    return {"status": "deleted", "id": history_id}


@router.delete("/search/history/clear", summary="Clear all search history for a user")
async def clear_search_history(user_id: str = Query(...)):
    await SearchHistory.find(SearchHistory.user_id == user_id).delete()
    return {"status": "cleared", "user_id": user_id}
