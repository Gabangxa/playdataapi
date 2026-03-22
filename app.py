import os
from flask import Flask, jsonify, request, render_template, g
from flask_cors import CORS
from google_play_scraper.exceptions import NotFoundError

from auth import require_auth
import scraper

app = Flask(__name__)
CORS(app)

# ---------------------------------------------------------------------------
# Infrastructure
# ---------------------------------------------------------------------------

@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/docs")
def docs():
    return render_template("docs.html")


# ---------------------------------------------------------------------------
# Core API — all protected by @require_auth
# ---------------------------------------------------------------------------

@app.route("/apps/<package_id>")
@require_auth
def get_app(package_id):
    lang = request.args.get("lang", "en")
    country = request.args.get("country", "us")
    try:
        data = scraper.get_app(package_id, lang=lang, country=country)
        return jsonify(data), 200
    except NotFoundError:
        return jsonify({"error": "App not found on Google Play", "code": "app_not_found"}), 404
    except Exception as e:
        app.logger.error(f"upstream error for {package_id}: {e}")
        return jsonify({"error": "Failed to fetch from Google Play", "code": "upstream_error"}), 502


@app.route("/apps/<package_id>/reviews")
@require_auth
def get_reviews(package_id):
    try:
        count = int(request.args.get("count", 20))
        count = min(max(count, 1), 100)
    except ValueError:
        return jsonify({"error": "'count' must be an integer", "code": "invalid_param"}), 400

    sort = request.args.get("sort", "newest")
    if sort not in ("newest", "most_relevant"):
        return jsonify({"error": "'sort' must be 'newest' or 'most_relevant'", "code": "invalid_param"}), 400

    lang = request.args.get("lang", "en")
    country = request.args.get("country", "us")

    try:
        reviews = scraper.get_reviews(package_id, count=count, sort=sort, lang=lang, country=country)
        return jsonify({"package_id": package_id, "count": len(reviews), "reviews": reviews}), 200
    except NotFoundError:
        return jsonify({"error": "App not found on Google Play", "code": "app_not_found"}), 404
    except Exception as e:
        app.logger.error(f"reviews error for {package_id}: {e}")
        return jsonify({"error": "Failed to fetch reviews", "code": "upstream_error"}), 502


@app.route("/apps/<package_id>/similar")
@require_auth
def get_similar(package_id):
    lang = request.args.get("lang", "en")
    country = request.args.get("country", "us")
    try:
        similar = scraper.get_similar(package_id, lang=lang, country=country)
        return jsonify({"package_id": package_id, "similar": similar}), 200
    except NotFoundError:
        return jsonify({"error": "App not found on Google Play", "code": "app_not_found"}), 404
    except Exception as e:
        app.logger.error(f"similar error for {package_id}: {e}")
        return jsonify({"error": "Failed to fetch similar apps", "code": "upstream_error"}), 502


@app.route("/search")
@require_auth
def search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "Query parameter 'q' is required", "code": "invalid_param"}), 400

    try:
        n = int(request.args.get("n", 20))
        n = min(max(n, 1), 50)
    except ValueError:
        return jsonify({"error": "'n' must be an integer", "code": "invalid_param"}), 400

    lang = request.args.get("lang", "en")
    country = request.args.get("country", "us")

    try:
        results = scraper.do_search(q, n=n, lang=lang, country=country)
        return jsonify({"query": q, "count": len(results), "results": results}), 200
    except Exception as e:
        app.logger.error(f"search error for '{q}': {e}")
        return jsonify({"error": "Search failed", "code": "upstream_error"}), 502


@app.route("/trending")
@require_auth
def trending():
    collection = request.args.get("collection", "top_free")
    if collection not in ("top_free", "top_paid", "top_grossing"):
        return jsonify({"error": "'collection' must be top_free, top_paid, or top_grossing", "code": "invalid_param"}), 400

    category = request.args.get("category") or None

    try:
        n = int(request.args.get("n", 20))
        n = min(max(n, 1), 100)
    except ValueError:
        return jsonify({"error": "'n' must be an integer", "code": "invalid_param"}), 400

    lang = request.args.get("lang", "en")
    country = request.args.get("country", "us")

    try:
        apps = scraper.get_trending(collection=collection, category=category, n=n, lang=lang, country=country)
        return jsonify({"collection": collection, "category": category, "count": len(apps), "apps": apps}), 200
    except Exception as e:
        app.logger.error(f"trending error: {e}")
        return jsonify({"error": "Failed to fetch trending data", "code": "upstream_error"}), 502


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port, debug=False)
