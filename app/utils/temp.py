# # backend/app/utils/xtream_service.py
# import httpx
# from app.models.content import Content, Season, Episode
# from datetime import datetime, timezone

# XC_URL = "http://slytv.uk:80"
# USERNAME = "yWYKAuE7"
# PASSWORD = "g1hGECF"

# BASE_API = f"{XC_URL}/player_api.php?username={USERNAME}&password={PASSWORD}"


# async def fetch_and_sync_xtream():
#     synced = {"movies": 0, "series": 0, "channels": 0}
 
#     try:
#         async with httpx.AsyncClient() as client:
#             # Fetch categories first to validate a successful connection
#             try:
#                 live_cats_res = await client.get(f"{BASE_API}&action=get_live_categories")
#                 live_cats_res.raise_for_status() # Raise an exception for bad status codes
#                 print("Successfully connected to Xtream API.")
#             except httpx.HTTPStatusError as exc:
#                 print(f"Failed to connect to Xtream API: {exc.response.status_code} - {exc.response.text}")
#                 return synced
#             except httpx.RequestError as exc:
#                 print(f"An error occurred while requesting Xtream API: {exc}")
#                 return synced

#             print("Fetching all content lists...")
#             movies_res = await client.get(f"{BASE_API}&action=get_vod_streams")
#             series_res = await client.get(f"{BASE_API}&action=get_series")
#             live_res = await client.get(f"{BASE_API}&action=get_live_streams")

#             movies = movies_res.json() if movies_res.status_code == 200 else []
#             series = series_res.json() if series_res.status_code == 200 else []
#             channels = live_res.json() if live_res.status_code == 200 else []
#             print("Content lists fetched successfully.")

#             # --------------------
#             # Sync movies
#             # --------------------
#             # for m in movies:
#             #     try:
#             #         stream_id = m.get("stream_id")
#             #         if not stream_id:
#             #             print(f"Skipping movie with no stream_id: {m.get('name')}")
#             #             continue
#             #         doc = Content(
#             #             name=m.get("name"),
#             #             content_type="movie",
#             #             stream_id=int(stream_id),
#             #             stream_url=f"{XC_URL}/movie/{USERNAME}/{PASSWORD}/{stream_id}.mp4",
#             #             category_id=str(m.get("category_id")),
#             #             poster=m.get("stream_icon"),
#             #             description=m.get("plot", ""),
#             #             last_updated=datetime.now(timezone.utc)
#             #         )
#             #         await Content.find_one({"content_type": "movie", "stream_id": doc.stream_id}).upsert(
#             #             {"$set": doc.model_dump(exclude_unset=True, by_alias=True)},
#             #             on_insert=doc
#             #         )
#             #         synced["movies"] += 1
#             #     except Exception as e:
#             #         print(f"Error processing movie {m.get('name')}: {e}")
#             #         continue

#             # --------------------
#             # Sync series (with seasons + episodes)
#             # --------------------
#             # for s in series:
#             #     try:
#             #         series_id = s.get("series_id")
#             #         if not series_id:
#             #             print(f"Skipping series with no ID: {s.get('name')}")
#             #             continue

#             #         series_info_res = await client.get(f"{BASE_API}&action=get_series_info&series_id={series_id}")
#             #         series_info = series_info_res.json() if series_info_res.status_code == 200 else {}
#             #         episodes_data = series_info.get("episodes", {})

#             #         # This is the crucial fix: check if episodes_data is a dict before iterating
#             #         if not isinstance(episodes_data, dict):
#             #             print(f"Skipping series {s.get('name')} due to invalid episode data format.")
#             #             continue

#             #         seasons = []
#             #         for season_number_str, eps in episodes_data.items():
#             #             eps_list = []
#             #             try:
#             #                 season_number = int(season_number_str)
#             #             except ValueError:
#             #                 print(f"Invalid season number for series {s.get('name')}: {season_number_str}")
#             #                 continue

#             #             for e in eps:
#             #                 ep_id = e.get("id")
#             #                 if not ep_id:
#             #                     print(f"Skipping episode with no ID in series {s.get('name')}")
#             #                     continue
                            
#             #                 eps_list.append(Episode(
#             #                     episode_num=e.get("episode_num"),
#             #                     title=e.get("title"),
#             #                     stream_id=int(ep_id),
#             #                     stream_url=f"{XC_URL}/series/{USERNAME}/{PASSWORD}/{series_id}/{ep_id}.{e.get('container_extension', 'mp4')}"
#             #                 ))
#             #             seasons.append(Season(season_number=season_number, episodes=eps_list))

#             #         doc = Content(
#             #             name=s.get("name"),
#             #             content_type="series",
#             #             stream_id=int(series_id),
#             #             category_id=str(s.get("category_id")),
#             #             poster=s.get("cover"),
#             #             description=s.get("plot", ""),
#             #             seasons=seasons,
#             #             last_updated=datetime.now(timezone.utc)
#             #         )
#             #         await Content.find_one({"content_type": "series", "stream_id": doc.stream_id}).upsert(
#             #             {"$set": doc.model_dump(exclude_unset=True, by_alias=True)},
#             #             on_insert=doc
#             #         )
#             #         synced["series"] += 1
#             #     except Exception as e:
#             #         print(f"Error processing series {s.get('name')}: {e}")
#             #         continue

#             # --------------------
#             # Sync channels (live TV)
#             # --------------------
#             print("Starting live channel sync...")

#             # Print the first channel's raw data for verification
#             if channels:
#                 print("\n--- First Live Channel Data (for inspection) ---")
#                 print(channels[0])
#                 print("--------------------------------------------------\n")

#             for c in channels:
#                 try:
#                     stream_id = c.get("stream_id")
#                     if not stream_id:
#                         print(f"Skipping channel with no stream_id: {c.get('name')}")
#                         continue
                    
#                     doc = Content(
#                         name=c.get("name"),
#                         content_type="channel",
#                         stream_id=int(stream_id),
#                         stream_url=f"{XC_URL}/live/{USERNAME}/{PASSWORD}/{stream_id}.ts",
#                         category_id=str(c.get("category_id")),
#                         poster=c.get("stream_icon"),
#                         last_updated=datetime.now(timezone.utc)
#                     )
#                     await Content.find_one({"content_type": "channel", "stream_id": doc.stream_id}).upsert(
#                         {"$set": doc.model_dump(exclude_unset=True, by_alias=True)},
#                         on_insert=doc
#                     )
#                     synced["channels"] += 1
#                     # Add a print statement to show progress
#                     if synced["channels"] % 100 == 0:
#                         print(f"Synced {synced['channels']} live channels.")
#                 except Exception as e:
#                     print(f"Error processing channel {c.get('name')}: {e}")
#                     continue

#         print("Syncing complete.")
#         return synced
#     except Exception as e:
#         print(f"An unexpected error occurred during the sync process: {e}")
#         # Always return the synced dict, even on failure
#         return synced

# backend/app/utils/xtream_service.py
import httpx
from app.models.content import Content, Season, Episode
from app.models.category import Category # Assuming you have this now
from datetime import datetime, timezone

XC_URL = "http://slytv.uk:80"
USERNAME = "yWYKAuE7"
PASSWORD = "g1hGECF"

BASE_API = f"{XC_URL}/player_api.php?username={USERNAME}&password={PASSWORD}"


async def fetch_and_sync_xtream(timeout=30.0):
    try:
        async with httpx.AsyncClient() as client:
            print("Starting data fetch and inspection...")

            # --- Fetching ALL Content Lists ---
            print("\n--- Fetching all content lists ---")
            movies_res = await client.get(f"{BASE_API}&action=get_vod_streams")
            series_res = await client.get(f"{BASE_API}&action=get_series")
            live_res = await client.get(f"{BASE_API}&action=get_live_streams")

            movies = movies_res.json() if movies_res.status_code == 200 else []
            series = series_res.json() if series_res.status_code == 200 else []
            channels = live_res.json() if live_res.status_code == 200 else []
            print("Content lists fetched successfully.")
            
            # --- Fetching Categories ---
            print("\n--- Fetching categories ---")
            movie_cats_res = await client.get(f"{BASE_API}&action=get_vod_categories")
            series_cats_res = await client.get(f"{BASE_API}&action=get_series_categories")
            live_cats_res = await client.get(f"{BASE_API}&action=get_live_categories")

            movie_cats = movie_cats_res.json() if movie_cats_res.status_code == 200 else []
            series_cats = series_cats_res.json() if series_cats_res.status_code == 200 else []
            live_cats = live_cats_res.json() if live_cats_res.status_code == 200 else []
            print("Category lists fetched successfully.")

            # --- Fetching EPG Data ---
            epg_data = []
            if channels:
                print("\n--- Fetching EPG for the first live channel ---")
                first_channel_id = channels[0].get("epg_channel_id")
                if first_channel_id:
                    epg_res = await client.get(f"{BASE_API}&action=get_short_epg&stream_id={first_channel_id}")
                    epg_data = epg_res.json() if epg_res.status_code == 200 else []
                    print("EPG data fetched successfully.")
                else:
                    print("First channel has no EPG channel ID. Skipping EPG fetch.")
            else:
                print("No live channels found. Skipping EPG fetch.")
            

            # --- Printing First 5 Items from each list ---
            print("\n" + "="*50)
            print("INSPECTION OF FIRST 5 ITEMS")
            print("="*50 + "\n")

            print("\n--- First 5 Movie Items ---")
            for item in movies[:5]:
                print(item)

            print("\n--- First 5 Series Items ---")
            for item in series[:5]:
                print(item)
            
            print("\n--- First 5 Live Channel Items ---")
            for item in channels[:5]:
                print(item)
                
            print("\n--- First 5 Movie Categories ---")
            for item in movie_cats[:5]:
                print(item)

            print("\n--- First 5 Series Categories ---")
            for item in series_cats[:5]:
                print(item)
                
            print("\n--- First 5 Live Categories ---")
            for item in live_cats[:5]:
                print(item)

            print("\n--- First 5 EPG Items ---")
            for item in epg_data[:5]:
                print(item)
                
            print("\n" + "="*50)
            print("DATA INSPECTION COMPLETE. NO DATABASE CHANGES WERE MADE.")
            print("="*50)

    except Exception as e:
        print(f"An unexpected error occurred during the fetch process: {e}")

""" main.py
import logging
from fastapi import FastAPI
from app.db import init_db
from app.utils.xtream_service import fetch_and_sync_xtream 

# ---------- Logging Setup ----------
logging.basicConfig(
    level=logging.DEBUG,  # or INFO if you prefer less noise
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
# Silence noisy pymongo logs
logging.getLogger("pymongo").setLevel(logging.WARNING)
logging.getLogger("pymongo.topology").setLevel(logging.WARNING)
logging.getLogger("pymongo.serverSelection").setLevel(logging.WARNING)
logging.getLogger("pymongo.connection").setLevel(logging.WARNING)
logging.getLogger("pymongo.command").setLevel(logging.WARNING)
logger = logging.getLogger("main")

# Import routers
from app.routes import auth, forgot_password, profile, payment, recommendation
from app.routes.content import router as content_router
from app.routes import watch_history
from app.routes import favorite
from app.routes import continue_watching  
from app.routes import search             

app = FastAPI(title="Upcomes TV Backend")

# ---------- Startup ----------
@app.on_event("startup")
async def on_startup():
    logger.info("App startup: initializing DB...")
    await init_db()
    logger.info("DB initialized.")

    # ➕ ADD THIS SECTION ➕
    logger.info("App startup: syncing content from Xtream server...")
    try:
        sync_result = await fetch_and_sync_xtream()
        logger.info(f"Content sync completed. Synced {sync_result['total_content']} items.")
    except Exception as e:
        logger.error(f"Failed to sync content on startup: {e}")
    # ➕ END OF ADDITION ➕


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

"""