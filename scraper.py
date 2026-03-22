import time
from google_play_scraper import app as gp_app, reviews as gp_reviews, search as gp_search
from google_play_scraper.features.top_chart import Collection, Category
from google_play_scraper import Sort
from google_play_scraper.exceptions import NotFoundError
from google_play_scraper import top_chart

CACHE = {}
CACHE_TTL = 3600       # 1 hour — app metadata
REVIEWS_TTL = 1800     # 30 min — reviews
SEARCH_TTL = 1800
TRENDING_TTL = 1800


def _cached(key, ttl, fetch_fn):
    now = time.time()
    if key in CACHE:
        ts, data = CACHE[key]
        if now - ts < ttl:
            return data
    data = fetch_fn()
    CACHE[key] = (now, data)
    return data


def get_app(package_id, lang="en", country="us"):
    """Fetch app metadata. Raises NotFoundError or Exception."""
    key = f"app:{package_id}:{lang}:{country}"
    def fetch():
        result = gp_app(package_id, lang=lang, country=country)
        return _format_app(result)
    return _cached(key, CACHE_TTL, fetch)


def _format_app(r):
    return {
        "package_id": r.get("appId"),
        "title": r.get("title"),
        "developer": r.get("developer"),
        "developer_id": r.get("developerId"),
        "category": r.get("genre"),
        "rating": r.get("score"),
        "ratings_count": r.get("ratings"),
        "installs": r.get("installs"),
        "price": r.get("price"),
        "free": r.get("free"),
        "description": r.get("description"),
        "last_updated": r.get("updated"),
        "version": r.get("version"),
        "android_version": r.get("androidVersion"),
        "icon_url": r.get("icon"),
    }


def get_reviews(package_id, count=20, sort="newest", lang="en", country="us"):
    key = f"reviews:{package_id}:{count}:{sort}:{lang}:{country}"
    sort_enum = Sort.NEWEST if sort == "newest" else Sort.MOST_RELEVANT

    def fetch():
        result, _ = gp_reviews(
            package_id,
            lang=lang,
            country=country,
            sort=sort_enum,
            count=count,
        )
        formatted = []
        for r in result:
            reply_text = None
            if r.get("replyContent"):
                reply_text = r["replyContent"]
            formatted.append({
                "review_id": r.get("reviewId"),
                "author": r.get("userName"),
                "rating": r.get("score"),
                "text": r.get("content"),
                "date": r.get("at").strftime("%Y-%m-%d") if r.get("at") else None,
                "thumbs_up": r.get("thumbsUpCount"),
                "reply": reply_text,
            })
        return formatted
    return _cached(key, REVIEWS_TTL, fetch)


def get_similar(package_id, lang="en", country="us"):
    # google-play-scraper doesn't expose similarApps directly via top-level api()
    # We fetch app details and use the genre to do a search as fallback
    app_data = gp_app(package_id, lang=lang, country=country)
    similar_raw = app_data.get("similarApps") or app_data.get("similar") or []

    results = []
    if similar_raw:
        for pid in similar_raw[:20]:
            try:
                a = gp_app(pid, lang=lang, country=country)
                results.append(_format_similar(a))
            except Exception:
                continue
    else:
        # Fallback: search by app title keywords
        title = app_data.get("title", "")
        search_results = gp_search(title, n_hits=10, lang=lang, country=country)
        for a in search_results:
            if a.get("appId") != package_id:
                results.append(_format_similar(a))
    return results


def _format_similar(r):
    return {
        "package_id": r.get("appId"),
        "title": r.get("title"),
        "developer": r.get("developer"),
        "rating": r.get("score"),
        "installs": r.get("installs"),
        "icon_url": r.get("icon"),
    }


def do_search(query, n=20, lang="en", country="us"):
    key = f"search:{query}:{n}:{lang}:{country}"

    def fetch():
        results = gp_search(query, n_hits=n, lang=lang, country=country)
        return [_format_similar(r) for r in results]
    return _cached(key, SEARCH_TTL, fetch)


_COLLECTION_MAP = {
    "top_free": Collection.TOP_FREE,
    "top_paid": Collection.TOP_PAID,
    "top_grossing": Collection.GROSSING,
}

_CATEGORY_MAP = {
    "MUSIC_AND_AUDIO": Category.MUSIC_AND_AUDIO,
    "GAMES": Category.GAME,
    "SOCIAL": Category.SOCIAL,
    "TOOLS": Category.TOOLS,
    "PRODUCTIVITY": Category.PRODUCTIVITY,
    "EDUCATION": Category.EDUCATION,
    "ENTERTAINMENT": Category.ENTERTAINMENT,
    "FINANCE": Category.FINANCE,
    "HEALTH_AND_FITNESS": Category.HEALTH_AND_FITNESS,
    "LIFESTYLE": Category.LIFESTYLE,
    "MAPS_AND_NAVIGATION": Category.MAPS_AND_NAVIGATION,
    "NEWS_AND_MAGAZINES": Category.NEWS_AND_MAGAZINES,
    "PHOTOGRAPHY": Category.PHOTOGRAPHY,
    "SHOPPING": Category.SHOPPING,
    "SPORTS": Category.SPORTS,
    "TRAVEL_AND_LOCAL": Category.TRAVEL_AND_LOCAL,
    "VIDEO_PLAYERS": Category.VIDEO_PLAYERS,
    "WEATHER": Category.WEATHER,
    "COMMUNICATION": Category.COMMUNICATION,
    "BUSINESS": Category.BUSINESS,
}


def get_trending(collection="top_free", category=None, n=20, lang="en", country="us"):
    key = f"trending:{collection}:{category}:{n}:{lang}:{country}"

    def fetch():
        coll = _COLLECTION_MAP.get(collection, Collection.TOP_FREE)
        cat = _CATEGORY_MAP.get(category) if category else None
        kwargs = dict(collection=coll, lang=lang, country=country)
        if cat is not None:
            kwargs["category"] = cat
        results = top_chart(**kwargs)
        out = []
        for i, r in enumerate(results[:n]):
            out.append({
                "rank": i + 1,
                "package_id": r.get("appId"),
                "title": r.get("title"),
                "developer": r.get("developer"),
                "rating": r.get("score"),
                "installs": r.get("installs"),
                "icon_url": r.get("icon"),
            })
        return out
    return _cached(key, TRENDING_TTL, fetch)
