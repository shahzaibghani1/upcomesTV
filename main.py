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
app.include_router(recommendation.router, prefix="/recommendations", tags=["Recommendations"])
app.include_router(watch_history.router, prefix="/watch-history", tags=["Watch History"])
app.include_router(favourite.router, prefix="/favorites", tags=["Favorites"])
app.include_router(continue_watching.router, prefix="/continue", tags=["Continue Watching"])
app.include_router(search.router, prefix="/search", tags=["Search"])
app.include_router(movie.router, prefix="/movies", tags=["Movies"])
app.include_router(series.router, prefix="/series", tags=["Series"])
app.include_router(live_channels.router, prefix="/channels", tags=["Channels"])
app.include_router(categories.router, prefix="/categories", tags=["Categories"])

# ---------- Root ----------
@app.get("/")
def root():
    return {"msg": "Upcomes TV Backend running"}

# VIDEO_DIR = "videos" 


# @app.get("/video/{filename}")
# async def stream_video(filename: str, request: Request):
#     file_path = os.path.join(VIDEO_DIR, filename)

#     if not os.path.exists(file_path):
#         raise HTTPException(status_code=404, detail="Video not found")

#     file_size = os.path.getsize(file_path)
#     range_header = request.headers.get("range", None)

#     if range_header is None:
#         start = 0
#         end = file_size - 1
#     else:
#         range_match = range_header.replace("bytes=", "").split("-")
#         start = int(range_match[0])
#         end = int(range_match[1]) if range_match[1] else file_size - 1

#     chunk_size = (end - start) + 1

#     def iterfile():
#         with open(file_path, "rb") as f:
#             f.seek(start)
#             remaining = chunk_size
#             while remaining > 0:
#                 data = f.read(min(1024 * 1024, remaining))  # 1MB chunks
#                 if not data:
#                     break
#                 remaining -= len(data)
#                 yield data

#     headers = {
#         "Content-Range": f"bytes {start}-{end}/{file_size}",
#         "Accept-Ranges": "bytes",
#         "Content-Length": str(chunk_size),
#         "Content-Type": "video/mp4"
#     }

#     return StreamingResponse(iterfile(), status_code=206, headers=headers)

# async def stream_video(url: str, range_header: str | None):
#     headers = {"Range": range_header} if range_header else {}
#     logger.info(f"➡️ Requesting origin with headers: {headers}")

#     async with httpx.AsyncClient(follow_redirects=True) as client:
#         origin = await client.get(url, headers=headers, timeout=None)
#         logger.info(f"✅ Origin replied {origin.status_code}")

#         if origin.status_code not in (200, 206):
#             raise HTTPException(502, f"Bad origin status: {origin.status_code}")

#         return origin


# CHUNK_SIZE = 1024 * 64  # 64KB chunks (sweet spot)


# @app.get("/proxy")
# async def proxy(request: Request, url: str):
#     client_ip = request.client.host
#     range_header = request.headers.get("Range")

#     logger.info(f"📥 Client {client_ip} requested URL: {url}")
#     logger.info(f"📡 Client Range header: {range_header}")

#     origin = await stream_video(url, range_header)
#     content_type = origin.headers.get("Content-Type", "application/octet-stream")
#     content_range = origin.headers.get("Content-Range")
#     content_length = origin.headers.get("Content-Length")

#     logger.info(f"🎞 Content-Type: {content_type}")
#     logger.info(f"📏 Content-Range: {content_range}")
#     logger.info(f"📦 Content-Length: {content_length}")

#     async def generate():
#         try:
#             async for chunk in origin.aiter_bytes():
#                 yield chunk
#         except Exception as e:
#             logger.error(f"❌ Client aborted: {e}")

#     return StreamingResponse(
#         generate(),
#         status_code=origin.status_code,
#         media_type=content_type,
#         headers={
#             "Accept-Ranges": "bytes",
#             "Content-Range": content_range or "",
#             "Content-Length": content_length or "",
#         }
#     )


