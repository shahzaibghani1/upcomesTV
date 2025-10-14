from fastapi import APIRouter, HTTPException
from bson import ObjectId
from app.db import channels_collection

router = APIRouter()


@router.get("/fetch")
async def get_channels_list():
    try:
        filter_query = {
            "name": {"$ne": None, "$ne": "", "$exists": True},
            "stream_icon": {"$ne": None, "$ne": "", "$exists": True},
            "stream_url": {"$ne": None, "$ne": "", "$exists": True}
        }

        projection = {
            "name": 1,
            "stream_icon": 1,
            "stream_type": 1,
            "_id": 1
        }

        cursor = channels_collection.find(filter_query, projection).limit(40)
        channels_list = await cursor.to_list(length=40)

        if not channels_list:
            raise HTTPException(status_code=404, detail="No channels found")

        for channel in channels_list:
            channel["_id"] = str(channel["_id"])
            # No need to add 'type' if 'stream_type' already exists
            if "stream_type" not in channel:
                channel["stream_type"] = "live_channel"

        return channels_list

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/fetch/{channel_id}")
async def get_channel_by_id(channel_id: str):
    try:
        if not ObjectId.is_valid(channel_id):
            raise HTTPException(status_code=400, detail="Invalid channel ID format")

        filter_query = {
            "_id": ObjectId(channel_id),
            "name": {"$ne": None, "$ne": "", "$exists": True},
            "stream_icon": {"$ne": None, "$ne": "", "$exists": True},
            "stream_url": {"$ne": None, "$ne": "", "$exists": True}
        }

        channel = await channels_collection.find_one(filter_query)

        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found")

        channel["_id"] = str(channel["_id"])
        # Again, ensure the key exists but don't duplicate
        if "stream_type" not in channel:
            channel["stream_type"] = "live_channel"

        return channel

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
