# backend/app/routes/recommendation.py
from fastapi import APIRouter, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from app.models.content_similarity import ContentSimilarity
from app.db import movies_collection, series_collection, channels_collection

router = APIRouter()


import random
from fastapi import HTTPException

# ... keep your existing imports and router definition ...

@router.get("/random", summary="Get random mixed recommendations")
async def get_random_recommendations():
    """
    Fetch up to 20 random items (movies, series, live channels combined).
    Uses the same filtering rules as each collection's /fetch endpoints.
    Returns items with: _id, name, image, type
    """
    try:
        # Use the same logical filters as your working endpoints, but with $nin for cleanliness
        movies_match = {
            "stream_icon": {"$exists": True, "$nin": [None, ""]},
            "stream_url": {"$exists": True, "$nin": [None, ""]},
            "container_extension": "mkv"
        }

        series_match = {
            "name": {"$exists": True, "$nin": [None, ""]},
            "cover": {"$exists": True, "$nin": [None, ""]},
            "seasons": {"$exists": True, "$ne": []}
        }

        channels_match = {
            "name": {"$exists": True, "$nin": [None, ""]},
            "stream_icon": {"$exists": True, "$nin": [None, ""]},
            "stream_url": {"$exists": True, "$nin": [None, ""]}
        }

        # Desired samples per collection (total ~20)
        desired_movies = 7
        desired_series = 7
        desired_channels = 6

        # Count available docs that match each filter, then take min(count, desired)
        movie_count = await movies_collection.count_documents(movies_match)
        series_count = await series_collection.count_documents(series_match)
        channel_count = await channels_collection.count_documents(channels_match)

        m_size = min(desired_movies, movie_count)
        s_size = min(desired_series, series_count)
        c_size = min(desired_channels, channel_count)

        movies = []
        series = []
        channels = []

        # Run pipelines only when size > 0
        if m_size > 0:
            movie_pipeline = [
                {"$match": movies_match},
                {"$sample": {"size": m_size}},
                {"$project": {"_id": 1, "name": 1, "stream_icon": 1}}
            ]
            movies = await movies_collection.aggregate(movie_pipeline).to_list(length=m_size)

        if s_size > 0:
            series_pipeline = [
                {"$match": series_match},
                {"$sample": {"size": s_size}},
                {"$project": {"_id": 1, "name": 1, "cover": 1}}
            ]
            series = await series_collection.aggregate(series_pipeline).to_list(length=s_size)

        if c_size > 0:
            channel_pipeline = [
                {"$match": channels_match},
                {"$sample": {"size": c_size}},
                {"$project": {"_id": 1, "name": 1, "stream_icon": 1}}
            ]
            channels = await channels_collection.aggregate(channel_pipeline).to_list(length=c_size)

        # Normalize fields, convert ObjectId -> str, add type + image
        normalized = []

        for m in movies:
            normalized.append({
                "_id": str(m["_id"]),
                "name": m.get("name"),
                "image": m.get("stream_icon"),
                "type": "movie"
            })

        for s in series:
            normalized.append({
                "_id": str(s["_id"]),
                "name": s.get("name"),
                "image": s.get("cover"),
                "type": "series"
            })

        for c in channels:
            normalized.append({
                "_id": str(c["_id"]),
                "name": c.get("name"),
                "image": c.get("stream_icon"),
                "type": "live"
            })

        # Shuffle so movies/series/live are mixed
        random.shuffle(normalized)

        # Return recommendations (200 + empty list if none found)
        return {"recommendations": normalized}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# @router.get("/{content_id}", summary="Get recommendations for a given content ID with pagination")
# async def recommendations_for_content(
#     content_id: str,
#     skip: int = Query(0, ge=0, description="Number of recommendations to skip"),
#     limit: int = Query(20, ge=1, le=100, description="Max recommendations to return"),
# ):
#     # Get all similarity records for this content
#     sims = await ContentSimilarity.find({"content_id": content_id}).to_list()
#     if not sims:
#         raise HTTPException(status_code=404, detail="No recommendations found")

#     # Sort by similarity score
#     sims_sorted = sorted(sims, key=lambda s: s.similarity_score, reverse=True)

#     # Collect unique content IDs
#     top_ids = []
#     for s in sims_sorted:
#         if s.similar_content_id not in top_ids:
#             top_ids.append(s.similar_content_id)

#     # Apply pagination
#     paginated_ids = top_ids[skip: skip + limit]

#     # Fetch content details
#     contents = []
#     for cid in paginated_ids:
#         c = await Content.get(cid)
#         if c:
#             contents.append(c)

#     return {
#         "total": len(top_ids),
#         "skip": skip,
#         "limit": limit,
#         "recommendations": [jsonable_encoder(c) for c in contents],
#     }
