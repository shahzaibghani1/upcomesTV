import os
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

# Import all Beanie models here
from app.models.user import User
from app.models.payment import Package
from app.models.payment import Subscription
from app.models.content import Content
from app.models.content_similarity import ContentSimilarity
from app.models.watch_history import WatchHistory
from app.models.favorite import Favorite
from app.models.continue_watching import ContinueWatching
from app.models.search_history import SearchHistory
from app.models.category import Category

# Newly added models
from app.models.movies import Movie
from app.models.series import Series
from app.models.live_channels import LiveChannel

# Load MongoDB connection details from env (fallback to local)
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "upcomes_tv")

client = AsyncIOMotorClient(MONGO_URL)
database = client[MONGO_DB]

movies_collection = database["movies"]
series_collection = database["series"]
channels_collection = database["tv_channels"]

# Init Beanie ODM
async def init_db():
    await init_beanie(
        database=database,
        document_models=[
            User,
            Package,
            Subscription,
            Content,
            ContentSimilarity,
            WatchHistory,
            Favorite,
            ContinueWatching,
            SearchHistory,
            Category,
            Movie,          
            Series,         
            LiveChannel     
        ]
    )
