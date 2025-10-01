# backend/app/routes/recommendation.py
from fastapi import APIRouter, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from app.models.content import Content
from app.models.content_similarity import ContentSimilarity

router = APIRouter()


@router.get("/{content_id}", summary="Get recommendations for a given content ID with pagination")
async def recommendations_for_content(
    content_id: str,
    skip: int = Query(0, ge=0, description="Number of recommendations to skip"),
    limit: int = Query(20, ge=1, le=100, description="Max recommendations to return"),
):
    # Get all similarity records for this content
    sims = await ContentSimilarity.find({"content_id": content_id}).to_list()
    if not sims:
        raise HTTPException(status_code=404, detail="No recommendations found")

    # Sort by similarity score
    sims_sorted = sorted(sims, key=lambda s: s.similarity_score, reverse=True)

    # Collect unique content IDs
    top_ids = []
    for s in sims_sorted:
        if s.similar_content_id not in top_ids:
            top_ids.append(s.similar_content_id)

    # Apply pagination
    paginated_ids = top_ids[skip: skip + limit]

    # Fetch content details
    contents = []
    for cid in paginated_ids:
        c = await Content.get(cid)
        if c:
            contents.append(c)

    return {
        "total": len(top_ids),
        "skip": skip,
        "limit": limit,
        "recommendations": [jsonable_encoder(c) for c in contents],
    }
