from fastapi import APIRouter, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Dict, Any
import os
from bson import ObjectId
from app.db import movies_collection

router = APIRouter()


def serialize_movie(movie_dict: Dict) -> Dict:
    """Convert ObjectId to string and rename stream_type -> type"""
    if '_id' in movie_dict:
        movie_dict['_id'] = str(movie_dict['_id'])
    if "stream_type" in movie_dict:
        movie_dict["type"] = movie_dict.pop("stream_type")  # rename
    else:
        movie_dict["type"] = "movie"
    return movie_dict


@router.get("/fetch")
async def get_movies():
    """Fetch movies with ID, name, stream_icon, and type"""
    try:
        filter_query = {
            "stream_icon": {"$ne": None, "$ne": "", "$exists": True},
            "stream_url": {"$ne": None, "$ne": "", "$exists": True},
            "container_extension": "mkv"
        }

        projection = {
            "name": 1,
            "stream_icon": 1,
            "stream_type": 1,  # we’ll rename this in serialize_movie()
            "_id": 1
        }

        cursor = movies_collection.find(filter_query, projection).limit(40)
        movies = await cursor.to_list(length=40)

        if not movies:
            raise HTTPException(status_code=404, detail="No movies found matching the criteria")

        # Rename stream_type -> type and convert _id
        serialized_movies = [serialize_movie(movie) for movie in movies]
        return serialized_movies

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/fetch/{movie_id}")
async def get_movie_by_id(movie_id: str):
    try:
        if not ObjectId.is_valid(movie_id):
            raise HTTPException(status_code=400, detail="Invalid movie ID format")

        filter_query = {
            "_id": ObjectId(movie_id),
            "stream_icon": {"$ne": None, "$ne": "", "$exists": True},
            "stream_url": {"$ne": None, "$ne": "", "$exists": True},
            "container_extension": "mkv"
        }

        movie = await movies_collection.find_one(filter_query)
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found or does not meet criteria")

        movie["_id"] = str(movie["_id"])
        if "stream_type" in movie:
            movie["type"] = movie.pop("stream_type")
        else:
            movie["type"] = "movie"
        return movie

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/featured_banner")
async def get_featured_banner():
    try:
        pipeline = [
            {
                "$match": {
                    "stream_icon": {"$ne": None, "$ne": "", "$exists": True},
                    "stream_url": {"$ne": None, "$ne": "", "$exists": True},
                    "container_extension": "mkv"
                }
            },
            {"$sample": {"size": 4}},
            {"$project": {"_id": 1, "stream_icon": 1, "stream_type": 1}}
        ]

        movies = await movies_collection.aggregate(pipeline).to_list(length=4)

        if not movies:
            raise HTTPException(status_code=404, detail="No featured movies found")

        for movie in movies:
            movie["_id"] = str(movie["_id"])
            if "stream_type" in movie:
                movie["type"] = movie.pop("stream_type")
            else:
                movie["type"] = "movie"

        return movies

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
