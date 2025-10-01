# backend/app/routes/content.py
from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional, List
from pydantic import BaseModel
from app.models.content import Content
from fastapi.encoders import jsonable_encoder
import random
from datetime import datetime, timezone
from app.utils.xtream_service_modified import fetch_and_sync_xtream_direct

# switched from mock to Xtream service
#from app.utils.xtream_service import fetch_and_sync_xtream  

router = APIRouter()

# Request / Response schemas
# ---------------------
class ContentIn(BaseModel):
    tmdb_id: Optional[str] = None
    name: str
    content_type: str
    stream_id: Optional[int] = None
    rating: Optional[float] = None
    genres: Optional[List[str]] = []
    cast: Optional[List[str]] = []
    director: Optional[str] = None
    category_id: Optional[str] = None
    description: Optional[str] = None
    poster: Optional[str] = None


# ====================================================
#  USER-FACING ENDPOINTS (frontend will consume these)
# ====================================================

@router.get("/browse", summary="Browse all content with filters & pagination")
async def browse_content(
    content_type: Optional[str] = Query(None, description="Filter by content_type (movie/series/channel)"),
    genre: Optional[str] = Query(None, description="Filter by genre"),
    q: Optional[str] = Query(None, description="Search in name (case-insensitive substring)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    query = {}
    if content_type:
        query["content_type"] = content_type
    if genre:
        query["genres"] = {"$in": [genre]}
    if q:
        query["name"] = {"$regex": q, "$options": "i"}

    skip = (page - 1) * page_size
    total = await Content.find(query).count()
    items = await Content.find(query).skip(skip).limit(page_size).to_list()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [jsonable_encoder(i) for i in items],
    }

# ➕ New Endpoint: Get featured content
@router.get("/featured", summary="Get a small selection of featured content")
async def featured_content():
    # Fetch all movies and series from the database
    featured_items = await Content.find(
        { "content_type": { "$in": ["movie", "series"] } }
    ).to_list()
    
    # Randomly select up to 4 items
    if len(featured_items) > 4:
        featured_items = random.sample(featured_items, 4)
    
    return [jsonable_encoder(c) for c in featured_items]


@router.get("/details/{content_id}", summary="Get detailed info for one content item")
async def content_details(content_id: str):
    doc = await Content.get(content_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Content not found")
    return jsonable_encoder(doc)


@router.get("/trending", summary="Get trending content with pagination")
async def trending_content(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    all_items = await Content.find_all().to_list()
    total = len(all_items)

    # shuffle so it's "trending/random"
    random.shuffle(all_items)

    skip = (page - 1) * page_size
    paginated_items = all_items[skip: skip + page_size]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "trending": [jsonable_encoder(c) for c in paginated_items],
    }


# ====================================================
#  ADMIN/INTERNAL ENDPOINTS (not for frontend users)
# ====================================================

@router.post("/", summary="Create new content (admin)")
async def create_content(payload: ContentIn):
    doc = Content(**payload.dict())
    await doc.insert()
    return {"status": "created", "id": str(doc.id)}


@router.put("/{content_id}", summary="Update content (admin)")
async def update_content(content_id: str, payload: ContentIn):
    doc = await Content.get(content_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Content not found")
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(doc, k, v)
    doc.last_updated = datetime.now(timezone.utc)
    await doc.save()
    return {"status": "updated", "id": content_id}


@router.delete("/{content_id}", summary="Delete content (admin)")
async def delete_content(content_id: str):
    doc = await Content.get(content_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Content not found")
    await doc.delete()
    return {"status": "deleted", "id": content_id}


# updated to use Xtream Codes fetcher
# @router.post("/sync", summary="Sync content from IPTV (Xtream Codes API)")
# async def sync_content():
#     result = await fetch_and_sync_xtream()
#     return {"status": "ok", "synced": result}


# @router.get("/fetchContent")
# async def fetchDataFromXtream():
#     result = await fetch_and_sync_xtream_direct(limit_per_category=500)
#     return result


