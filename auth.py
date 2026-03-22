import os
import time
from datetime import datetime, timezone
from functools import wraps
from flask import request, jsonify, g

VALID_KEYS = set(k.strip() for k in os.environ.get("VALID_API_KEYS", "demo-key-123,test-key-456").split(",") if k.strip())

# { key: {"count": int, "last_reset": float, "last_request": float} }
_rate_store = {}

FREE_DAILY_LIMIT = 100
MIN_INTERVAL = 1.0  # seconds between requests


def _get_midnight_utc():
    now = datetime.now(timezone.utc)
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    # next midnight
    next_midnight = midnight.timestamp() + 86400
    return next_midnight


def _reset_if_needed(key):
    now = time.time()
    entry = _rate_store.get(key)
    if entry is None or now >= entry["last_reset"] + 86400:
        _rate_store[key] = {
            "count": 0,
            "last_reset": _get_start_of_day(),
            "last_request": 0,
        }
    return _rate_store[key]


def _get_start_of_day():
    now = datetime.now(timezone.utc)
    return now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()


def check_auth_and_rate_limit():
    """Returns (api_key, error_response, status_code) — error_response is None on success."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None, jsonify({"error": "Missing or invalid Authorization header", "code": "auth_required"}), 401

    key = auth_header[len("Bearer "):]
    if key not in VALID_KEYS:
        return None, jsonify({"error": "Invalid API key", "code": "auth_required"}), 401

    entry = _reset_if_needed(key)
    now = time.time()

    # 1 req/sec throttle
    elapsed = now - entry["last_request"]
    if elapsed < MIN_INTERVAL and entry["last_request"] != 0:
        remaining = FREE_DAILY_LIMIT - entry["count"]
        reset_ts = int(entry["last_reset"] + 86400)
        resp = jsonify({"error": "Rate limit exceeded (1 req/sec)", "code": "rate_limit"})
        resp.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        resp.headers["X-RateLimit-Reset"] = str(reset_ts)
        return None, resp, 429

    if entry["count"] >= FREE_DAILY_LIMIT:
        reset_ts = int(entry["last_reset"] + 86400)
        resp = jsonify({"error": "Daily rate limit exceeded", "code": "rate_limit"})
        resp.headers["X-RateLimit-Remaining"] = "0"
        resp.headers["X-RateLimit-Reset"] = str(reset_ts)
        return None, resp, 429

    entry["count"] += 1
    entry["last_request"] = now

    g.api_key = key
    g.rate_remaining = FREE_DAILY_LIMIT - entry["count"]
    g.rate_reset = int(entry["last_reset"] + 86400)
    return key, None, None


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        key, err, status = check_auth_and_rate_limit()
        if err is not None:
            return err, status
        response = f(*args, **kwargs)
        # Attach rate limit headers if response is a tuple or Response
        if isinstance(response, tuple):
            resp_obj, code = response[0], response[1]
            resp_obj.headers["X-RateLimit-Remaining"] = str(g.rate_remaining)
            resp_obj.headers["X-RateLimit-Reset"] = str(g.rate_reset)
        else:
            response.headers["X-RateLimit-Remaining"] = str(g.rate_remaining)
            response.headers["X-RateLimit-Reset"] = str(g.rate_reset)
        return response
    return decorated
