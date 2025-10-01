# backend/app/utils/xtream_service.py
import httpx
from datetime import datetime, timezone
from typing import List, Dict, Any
import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

# MongoDB connection
client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client["upcomes_tv"]
content_collection = db["content"]

XC_URL = "http://slytv.uk:80"
USERNAME = "yWYKAuE7"
PASSWORD = "g1hGECF"

BASE_API = f"{XC_URL}/player_api.php?username={USERNAME}&password={PASSWORD}"


async def fetch_limited_data(client: httpx.AsyncClient, action: str, limit: int = 500) -> List[Dict]:
    """Fetch limited data from Xtream API"""
    try:
        url = f"{BASE_API}&action={action}"
        response = await client.get(url)
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch {action}: {response.status_code}")
            return []
        
        data = response.json()
        return data[:limit] if isinstance(data, list) else []
    
    except Exception as e:
        logger.error(f"Error fetching {action}: {str(e)}")
        return []


def prepare_movie_document(movie_data: Dict) -> Dict:
    """Prepare movie document for MongoDB"""
    return {
        "name": movie_data.get("name"),
        "content_type": "movie",
        "stream_id": str(movie_data.get("stream_id")),
        "stream_url": f"{XC_URL}/movie/{USERNAME}/{PASSWORD}/{movie_data.get('stream_id')}.mp4",
        "category_id": str(movie_data.get("category_id")),
        "poster": movie_data.get("stream_icon"),
        "description": movie_data.get("plot", ""),
        "rating": movie_data.get("rating"),
        "year": movie_data.get("year"),
        "duration": movie_data.get("duration"),
        "last_updated": datetime.now(timezone.utc)
    }


async def prepare_series_document(client: httpx.AsyncClient, series_data: Dict) -> Dict:
    """Prepare series document with seasons and episodes"""
    series_id = series_data.get("series_id")
    seasons = []
    
    try:
        # Fetch series details
        series_info_res = await client.get(
            f"{BASE_API}&action=get_series_info&series_id={series_id}"
        )
        
        if series_info_res.status_code == 200:
            series_info = series_info_res.json()
            episodes_data = series_info.get("episodes", {})
            
            # Process seasons and episodes
            for season_number, eps in list(episodes_data.items())[:10]:  # Limit seasons
                episodes = []
                for episode in eps[:50]:  # Limit episodes per season
                    episodes.append({
                        "episode_num": episode.get("episode_num"),
                        "title": episode.get("title"),
                        "stream_id": episode.get("id"),
                        "stream_url": f"{XC_URL}/series/{USERNAME}/{PASSWORD}/{series_id}/{episode.get('id')}.{episode.get('container_extension', 'mp4')}",
                        "duration": episode.get("duration"),
                        "plot": episode.get("plot", "")
                    })
                
                seasons.append({
                    "season_number": int(season_number),
                    "episodes": episodes
                })
    
    except Exception as e:
        logger.error(f"Error processing series {series_id}: {str(e)}")
    
    return {
        "name": series_data.get("name"),
        "content_type": "series",
        "stream_id": str(series_id),
        "category_id": str(series_data.get("category_id")),
        "poster": series_data.get("cover"),
        "description": series_data.get("plot", ""),
        "seasons": seasons,
        "rating": series_data.get("rating"),
        "year": series_data.get("releaseDate"),
        "last_updated": datetime.now(timezone.utc)
    }


def prepare_channel_document(channel_data: Dict) -> Dict:
    """Prepare channel document for MongoDB"""
    return {
        "name": channel_data.get("name"),
        "content_type": "channel",
        "stream_id": str(channel_data.get("stream_id")),
        "stream_url": f"{XC_URL}/live/{USERNAME}/{PASSWORD}/{channel_data.get('stream_id')}.ts",
        "category_id": str(channel_data.get("category_id")),
        "poster": channel_data.get("stream_icon"),
        "description": channel_data.get("plot", ""),
        "last_updated": datetime.now(timezone.utc)
    }


async def bulk_insert_documents(documents: List[Dict], batch_size: int = 100):
    """Bulk insert documents into MongoDB"""
    try:
        # Using insert_many for better performance
        result = await content_collection.insert_many(documents)
        logger.info(f"Inserted {len(result.inserted_ids)} documents")
        return len(result.inserted_ids)
    except Exception as e:
        logger.error(f"Error bulk inserting documents: {str(e)}")
        return 0


async def clear_collection():
    """Clear the entire collection"""
    try:
        await content_collection.delete_many({})
        logger.info("Collection cleared")
    except Exception as e:
        logger.error(f"Error clearing collection: {str(e)}")


async def fetch_and_sync_xtream_direct(limit_per_category: int = 500):
    """
    Direct MongoDB implementation without models
    """
    start_time = datetime.now(timezone.utc)
    logger.info("Starting Xtream data sync with direct MongoDB...")
    
    # Clear old data
    await clear_collection()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Fetch data concurrently
        movies_task = fetch_limited_data(client, "get_vod_streams", limit_per_category)
        series_task = fetch_limited_data(client, "get_series", limit_per_category)
        live_task = fetch_limited_data(client, "get_live_streams", limit_per_category)
        
        movies, series, channels = await asyncio.gather(movies_task, series_task, live_task)
        
        synced = {"movies": 0, "series": 0, "channels": 0}
        all_documents = []
        
        # Process movies
        logger.info(f"Processing {len(movies)} movies...")
        movie_documents = [prepare_movie_document(movie) for movie in movies]
        all_documents.extend(movie_documents)
        synced["movies"] = len(movie_documents)
        
        # Process series
        logger.info(f"Processing {len(series)} series...")
        semaphore = asyncio.Semaphore(5)
        
        async def process_series_with_limit(series_data):
            async with semaphore:
                return await prepare_series_document(client, series_data)
        
        series_documents = await asyncio.gather(
            *[process_series_with_limit(series_data) for series_data in series],
            return_exceptions=True
        )
        
        # Filter out exceptions
        valid_series_documents = [
            doc for doc in series_documents 
            if not isinstance(doc, Exception) and doc is not None
        ]
        all_documents.extend(valid_series_documents)
        synced["series"] = len(valid_series_documents)
        
        # Process channels
        logger.info(f"Processing {len(channels)} channels...")
        channel_documents = [prepare_channel_document(channel) for channel in channels]
        all_documents.extend(channel_documents)
        synced["channels"] = len(channel_documents)
        
        # Bulk insert all documents
        logger.info(f"Inserting {len(all_documents)} total documents...")
        inserted_count = await bulk_insert_documents(all_documents)
        
        # Create indexes for better query performance
        await content_collection.create_index("content_type")
        await content_collection.create_index("category_id")
        await content_collection.create_index("stream_id")
        await content_collection.create_index("name")
        
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        logger.info(f"Sync completed in {duration:.2f} seconds: {synced}")
        
        return synced


# Query examples without models
async def query_content_direct():
    """Example queries using direct MongoDB operations"""
    
    # Get all movies
    movies = await content_collection.find({"content_type": "movie"}).to_list(length=100)
    
    # Get series with seasons
    series = await content_collection.find({"content_type": "series"}).to_list(length=100)
    
    # Search by name
    search_results = await content_collection.find(
        {"name": {"$regex": "action", "$options": "i"}}
    ).to_list(length=50)
    
    # Get by category
    category_content = await content_collection.find(
        {"category_id": "1"}
    ).to_list(length=100)
    
    return {
        "movies": movies,
        "series": series,
        "search_results": search_results,
        "category_content": category_content
    }