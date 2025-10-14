from fastapi import APIRouter, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from app.db import series_collection

router = APIRouter()

@router.get("/fetch")
async def get_series():
    try:
        filter_query = {
            "name": {"$ne": None, "$ne": "", "$exists": True},
            "cover": {"$ne": None, "$ne": "", "$exists": True},
            "seasons": {"$ne": [], "$exists": True}
        }

        projection = {
            "name": 1,
            "cover": 1,
            "_id": 1
        }

        cursor = series_collection.find(filter_query, projection).limit(40)
        series_list = await cursor.to_list(length=40)

        if not series_list:
            raise HTTPException(status_code=404, detail="No series found")

        for series in series_list:
            series["_id"] = str(series["_id"])
            series["type"] = "series"  # Explicitly add type

        return series_list

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/fetch/{series_id}")
async def get_series_by_id(series_id: str):
    try:
        if not ObjectId.is_valid(series_id):
            raise HTTPException(status_code=400, detail="Invalid series ID format")

        filter_query = {
            "_id": ObjectId(series_id),
            "name": {"$ne": None, "$ne": "", "$exists": True},
            "cover": {"$ne": None, "$ne": "", "$exists": True},
            "seasons": {"$ne": [], "$exists": True}
        }

        series = await series_collection.find_one(filter_query)

        if not series:
            raise HTTPException(status_code=404, detail="Series not found")

        series["_id"] = str(series["_id"])
        series["type"] = "series"
        return series

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
