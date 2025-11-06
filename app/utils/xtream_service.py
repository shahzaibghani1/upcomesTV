# backend/app/utils/xtream_service.py
import httpx
from datetime import datetime, timezone
from app.models.movies import Movie
from app.models.series import Series, Season, Episode
from app.models.live_channels import LiveChannel
from app.models.category import Category
import asyncio

XC_URL = "http://slytv.uk:80"
USERNAME = "yWYKAuE7"
PASSWORD = "g1hGECF"

BASE_API = f"{XC_URL}/player_api.php?username={USERNAME}&password={PASSWORD}"

# --------------------
# Categories (unchanged)
# --------------------
async def fetch_and_sync_categories(content_type: str):
    """
    Fetch and store categories for movies, series, or live.
    content_type: "movie", "series", "live"
    """
    endpoint_map = {
        "movie": "get_vod_categories",
        "series": "get_series_categories",
        "live": "get_live_categories",
    }

    if content_type not in endpoint_map:
        raise ValueError("Invalid content_type. Must be movie, series, or live")

    async with httpx.AsyncClient() as client:
        res = await client.get(f"{BASE_API}&action={endpoint_map[content_type]}")
        categories = res.json() if res.status_code == 200 else []

        print(f"📡 Fetching {content_type} categories → {len(categories)} items")

        for cat in categories:
            try:
                doc = Category(
                    category_id=str(cat.get("category_id")),
                    category_name=cat.get("category_name"),
                    parent_id=cat.get("parent_id", 0),
                )
                print(f"➡️ Saving category: {doc.category_name} (ID={doc.category_id})")

                await Category.find_one(Category.category_id == doc.category_id).upsert(
                    {"$set": doc.model_dump(exclude_unset=True)},
                    on_insert=doc,
                )
            except Exception as e:
                print(f"❌ Error saving category {cat.get('category_name')}: {e}")

        print(f"✅ Synced {len(categories)} {content_type} categories")
        return len(categories)


# --------------------
# Helper function with retry
# --------------------
async def fetch_with_retry(url, retries=3, timeout=10):
    for attempt in range(1, retries + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                res = await client.get(url)
                if res.status_code == 200:
                    return res.json()
                else:
                    print(f"⚠️ Warning: Status {res.status_code} for {url}")
        except Exception as e:
            print(f"⚠️ Attempt {attempt} failed for {url}: {e}")
        await asyncio.sleep(2)
    print(f"❌ All {retries} retries failed for {url}")
    return None


# --------------------
# Movies
# --------------------
async def fetch_and_sync_movies(category_id: str):
    url = f"{BASE_API}&action=get_vod_streams&category_id={category_id}"
    movies = await fetch_with_retry(url) or []

    category = await Category.find_one(Category.category_id == category_id)
    category_name = category.category_name if category else None

    print(f"📡 Fetching movies for category_id={category_id} ({category_name}) → {len(movies)} items")

    for m in movies:
        try:
            stream_id = m.get("stream_id")
            if not stream_id:
                print(f"⚠️ Skipping movie without stream_id: {m}")
                continue

            extension = m.get("container_extension", "mp4")
            stream_url = f"{XC_URL}/movie/{USERNAME}/{PASSWORD}/{stream_id}.{extension}"

            doc = Movie(
                tmdb_id=str(m.get("tmdb")) if m.get("tmdb") is not None else None,
                name=m.get("name"),
                stream_id=int(stream_id),
                stream_type="movie",
                stream_icon=m.get("stream_icon"),
                stream_url=stream_url,
                rating=float(m.get("rating", 0)) if m.get("rating") else None,
                trailer=m.get("trailer"),
                category_id=str(m.get("category_id")),
                category_name=m.get("category_name") or category_name,
                container_extension=extension,
                is_adult=bool(m.get("is_adult", 0)),
                added=datetime.fromtimestamp(int(m.get("added", 0)), tz=timezone.utc)
                if m.get("added")
                else None,
            )

            print(f"➡️ Saving movie: {doc.name} | ID={doc.stream_id} | URL={doc.stream_url}")

            await Movie.find_one(Movie.stream_id == doc.stream_id).upsert(
                {"$set": doc.model_dump(exclude_unset=True)},
                on_insert=doc,
            )
        except Exception as e:
            print(f"❌ Error saving movie {m.get('name')} (ID={m.get('stream_id')}): {e}")

    print(f"✅ Synced {len(movies)} movies from category {category_id}")
    return len(movies)


# --------------------
# Series
# --------------------
async def fetch_and_sync_series(category_id: str):
    url = f"{BASE_API}&action=get_series&category_id={category_id}"
    series_list = await fetch_with_retry(url) or []

    category = await Category.find_one(Category.category_id == category_id)
    category_name = category.category_name if category else None

    print(f"📡 Fetching series for category_id={category_id} ({category_name}) → {len(series_list)} items")

    for s in series_list:
        try:
            series_id = s.get("series_id")
            if not series_id:
                print(f"⚠️ Skipping series without series_id: {s}")
                continue

            info_url = f"{BASE_API}&action=get_series_info&series_id={series_id}"
            series_info = await fetch_with_retry(info_url) or {}
            episodes_data = series_info.get("episodes", {})
            seasons = []

            if isinstance(episodes_data, dict):
                for season_num, eps in episodes_data.items():
                    eps_list = []
                    for e in eps:
                        ep_id = e.get("id")
                        if not ep_id:
                            print(f"⚠️ Skipping episode without id in series {series_id}")
                            continue
                        extension = e.get("container_extension", "mp4")
                        eps_list.append(
                            Episode(
                                episode_num=int(e.get("episode_num", 0)),
                                title=e.get("title"),
                                stream_id=int(ep_id),
                                stream_url=f"{XC_URL}/series/{USERNAME}/{PASSWORD}/{ep_id}.{extension}",
                                added=datetime.fromtimestamp(int(e.get("added", 0)), tz=timezone.utc)
                                if e.get("added")
                                else None,
                            )
                        )
                    print(f"   ➡️ Season {season_num}: {len(eps_list)} episodes")
                    seasons.append(Season(season_number=int(season_num), episodes=eps_list))

            doc = Series(
                series_id=int(series_id),
                tmdb_id=str(s.get("tmdb")) if s.get("tmdb") is not None else None, 
                name=s.get("name"),
                cover=s.get("cover"),
                plot=s.get("plot"),
                cast=[c.strip() for c in s.get("cast", "").split(",")] if s.get("cast") else [], 
                director=s.get("director"),
                genre=[g.strip() for g in s.get("genre", "").split(",")] if s.get("genre") else [], 
                release_date=datetime.strptime(s.get("release_date"), "%Y-%m-%d").date() if s.get("release_date") else None, 
                last_modified=datetime.fromtimestamp(int(s.get("last_modified")), tz=timezone.utc) if s.get("last_modified") else None, 
                rating=float(s.get("rating", 0)) if s.get("rating") else None,
                trailer=s.get("youtube_trailer"), 
                episode_run_time=int(s.get("episode_run_time")) if s.get("episode_run_time") else None, 
                category_id=str(s.get("category_id")),
                category_name=s.get("category_name") or category_name,
                stream_url=None,
                seasons=seasons,
            )

            print(f"➡️ Saving series: {doc.name} | ID={doc.series_id} | Seasons={len(seasons)}")

            await Series.find_one(Series.series_id == doc.series_id).upsert(
                {"$set": doc.model_dump(exclude_unset=True)},
                on_insert=doc,
            )
        except Exception as e:
            print(f"❌ Error saving series {s.get('name')} (ID={s.get('series_id')}): {e}")

    print(f"✅ Synced {len(series_list)} series from category {category_id}")
    return len(series_list)


# --------------------
# Live Channels
# --------------------
async def fetch_and_sync_live_channels(category_id: str):
    url = f"{BASE_API}&action=get_live_streams&category_id={category_id}"
    channels = await fetch_with_retry(url) or []

    category = await Category.find_one(Category.category_id == category_id)
    category_name = category.category_name if category else None

    print(f"📡 Fetching live channels for category_id={category_id} ({category_name}) → {len(channels)} items")

    for c in channels:
        try:
            stream_id = c.get("stream_id")
            if not stream_id:
                print(f"⚠️ Skipping channel without stream_id: {c}")
                continue

            stream_url = f"{XC_URL}/live/{USERNAME}/{PASSWORD}/{stream_id}.ts"

            doc = LiveChannel(
                stream_id=int(stream_id),
                name=c.get("name"),
                stream_type="live",
                stream_icon=c.get("stream_icon"),
                stream_url=stream_url,
                epg_channel_id=c.get("epg_channel_id"),
                category_id=str(c.get("category_id")),
                category_name=c.get("category_name") or category_name,
                is_adult=bool(c.get("is_adult", 0)),
                tv_archive=c.get("tv_archive"),
                tv_archive_duration=c.get("tv_archive_duration"),
                direct_source=c.get("direct_source"),
                added=datetime.fromtimestamp(int(c.get("added", 0)), tz=timezone.utc)
                if c.get("added")
                else None,
            )

            print(f"➡️ Saving channel: {doc.name} | ID={doc.stream_id} | URL={doc.stream_url}")

            await LiveChannel.find_one(LiveChannel.stream_id == doc.stream_id).upsert(
                {"$set": doc.model_dump(exclude_unset=True)},
                on_insert=doc,
            )
        except Exception as e:
            print(f"❌ Error saving channel {c.get('name')} (ID={c.get('stream_id')}): {e}")

    print(f"✅ Synced {len(channels)} live channels from category {category_id}")
    return len(channels)
