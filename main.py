# backend/main.py
import logging
from fastapi import FastAPI
from app.db import init_db
from app.utils.xtream_service import (
    fetch_and_sync_categories,
    fetch_and_sync_movies,
    fetch_and_sync_series,
    fetch_and_sync_live_channels,
)
from fastapi.middleware.cors import CORSMiddleware
from app.models.category import Category
import aiohttp
from fastapi import Request, HTTPException
from fastapi.responses import StreamingResponse
import httpx
import logging
import os
from fastapi.staticfiles import StaticFiles



# ---------- Logging Setup ----------
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
log = logging.getLogger("proxy")
logging.getLogger("pymongo").setLevel(logging.INFO)
logging.getLogger("pymongo.topology").setLevel(logging.INFO)
logging.getLogger("pymongo.serverSelection").setLevel(logging.INFO)
logging.getLogger("pymongo.connection").setLevel(logging.INFO)
logging.getLogger("pymongo.command").setLevel(logging.INFO)
logging.getLogger("passlib.utils.compat").setLevel(logging.INFO)
logging.getLogger("passlib.registry").setLevel(logging.INFO)
logger = logging.getLogger("main")


# Import routers
from app.routes import auth, favourite, forgot_password, live_channels, movie, profile, payment, recommendation, series, categories
from app.routes import watch_history, continue_watching, search

app = FastAPI(title="Upcomes TV Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for testing; restrict later
    allow_credentials=True,
    allow_methods=["*"],  # <– THIS handles OPTIONS requests!
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")



# ---------- Startup ----------
@app.on_event("startup")
async def on_startup():
    await init_db()
    logger.info("DB initialized.")

    try:
        # 1) Fetch all categories from Xtream
        #await fetch_and_sync_categories("movie")
        #await fetch_and_sync_categories("series")
        #await fetch_and_sync_categories("live")

        # 2) Get all categories from DB and sync their content

        # # Movies
        # movie_cats = await Category.find().to_list()
        # for cat in movie_cats:
        #     logger.info(f"🎬 Syncing movies for category: {cat.category_name} ({cat.category_id})")
        #     await fetch_and_sync_movies(cat.category_id)

        # # Series
        # series_cats = await Category.find().to_list()
        # for cat in series_cats:
        #     logger.info(f"📺 Syncing series for category: {cat.category_name} ({cat.category_id})")
        #     await fetch_and_sync_series(cat.category_id)

        # # Live Channels
        # live_cats = await Category.find().to_list()
        # for cat in live_cats:
        #     logger.info(f"📡 Syncing live channels for category: {cat.category_name} ({cat.category_id})")
        #     await fetch_and_sync_live_channels(cat.category_id)

        logger.info("✅ All content synced successfully.")

    except Exception as e:
        logger.error(f"Content sync failed: {e}")

# ---------- Routers ----------
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(forgot_password.router, prefix="/password", tags=["Password Management"])
app.include_router(profile.router, prefix="/profile", tags=["Profile"])
app.include_router(payment.router, prefix="/payment", tags=["Payment"])
app.include_router(recommendation.router, prefix="/recommendations", tags=["Recommendations"])
app.include_router(watch_history.router, prefix="/watch-history", tags=["Watch History"])
app.include_router(favourite.router, prefix="/favorites", tags=["Favorites"])
app.include_router(continue_watching.router, prefix="/continue", tags=["Continue Watching"])
app.include_router(search.router, prefix="/search", tags=["Search"])
app.include_router(movie.router, prefix="/movies", tags=["Movies"])
app.include_router(series.router, prefix="/series", tags=["Series"])
app.include_router(live_channels.router, prefix="/channels", tags=["Channels"])
app.include_router(categories.router, prefix="/categories", tags=["Categories"])

@app.get("/fetch-series")
async def save_series_again():
    try:
        await fetch_and_sync_categories("series")
        # Series
        series_cats = await Category.find().to_list()
        for cat in series_cats:
            logger.info(f"📺 Syncing series for category: {cat.category_name} ({cat.category_id})")
            await fetch_and_sync_series(cat.category_id)



        logger.info("✅ All content synced successfully.")

    except Exception as e:
        logger.error(f"Content sync failed: {e}")

# ---------- Root ----------
@app.get("/")
def root():
    return {"msg": "Upcomes TV Backend running"}
