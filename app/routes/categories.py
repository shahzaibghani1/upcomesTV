from fastapi import APIRouter, HTTPException
from app.db import category_collection, movies_collection, series_collection, channels_collection
from bson import ObjectId

router = APIRouter()

@router.get("/fetch_all")
async def get_all_categories():
    try:
        # Movies categories
        movie_categories = await movies_collection.aggregate([
            {
                "$match": {
                    "category_id": {"$exists": True, "$ne": "", "$ne": None},
                    "category_name": {"$exists": True, "$ne": "", "$ne": None},
                }
            },
            {
                "$group": {
                    "_id": "$category_id",
                    "category_name": {"$first": "$category_name"}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "category_id": "$_id",
                    "category_name": 1
                }
            }
        ]).to_list(length=None)

        # Series categories
        series_categories = await series_collection.aggregate([
            {
                "$match": {
                    "category_id": {"$exists": True, "$ne": "", "$ne": None},
                    "category_name": {"$exists": True, "$ne": "", "$ne": None},
                }
            },
            {
                "$group": {
                    "_id": "$category_id",
                    "category_name": {"$first": "$category_name"}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "category_id": "$_id",
                    "category_name": 1
                }
            }
        ]).to_list(length=None)

        # Live channels categories
        live_categories = await channels_collection.aggregate([
            {
                "$match": {
                    "category_id": {"$exists": True, "$ne": "", "$ne": None},
                    "category_name": {"$exists": True, "$ne": "", "$ne": None},
                }
            },
            {
                "$group": {
                    "_id": "$category_id",
                    "category_name": {"$first": "$category_name"}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "category_id": "$_id",
                    "category_name": 1
                }
            }
        ]).to_list(length=None)

        return {
            "movies": movie_categories,
            "series": series_categories,
            "live_channels": live_categories
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")