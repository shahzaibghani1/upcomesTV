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
from app.models.category import Category

# ---------- Logging Setup ----------
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logging.getLogger("pymongo").setLevel(logging.WARNING)
logger = logging.getLogger("main")

# Import routers
from app.routes import auth, forgot_password, profile, payment, recommendation
from app.routes.content import router as content_router
from app.routes import watch_history, favorite, continue_watching, search

app = FastAPI(title="Upcomes TV Backend")

# ---------- Startup ----------
@app.on_event("startup")
async def on_startup():
    logger.info("App startup: initializing DB...")
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
app.include_router(content_router, prefix="/content", tags=["Content"])
app.include_router(recommendation.router, prefix="/recommendations", tags=["Recommendations"])
app.include_router(watch_history.router, prefix="/watch-history", tags=["Watch History"])
app.include_router(favorite.router, prefix="/favorites", tags=["Favorites"])
app.include_router(continue_watching.router, prefix="/continue", tags=["Continue Watching"])
app.include_router(search.router, prefix="/content", tags=["Search"])

# ---------- Root ----------
@app.get("/")
def root():
    return {"msg": "Upcomes TV Backend running"}
