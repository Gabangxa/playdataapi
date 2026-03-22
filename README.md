# PlayDataAPI

Google Play ASO Data API for indie mobile developers. Get app metadata, reviews, keyword rankings, and trending charts via a clean REST API.

## What is PlayDataAPI?

PlayDataAPI wraps Google Play public app data into a developer-first REST API. No scraping setup, no headless browsers — just one `Bearer` token and you're fetching live app data.

## Quick Start

```bash
# App details
curl https://your-app.replit.app/apps/com.spotify.music \
  -H "Authorization: Bearer demo-key-123"

# Search by keyword
curl "https://your-app.replit.app/search?q=music+player" \
  -H "Authorization: Bearer demo-key-123"

# Top free charts
curl "https://your-app.replit.app/trending?collection=top_free&n=10" \
  -H "Authorization: Bearer demo-key-123"
```

## All Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/apps/{package_id}` | Full app metadata |
| GET | `/apps/{package_id}/reviews` | User reviews |
| GET | `/apps/{package_id}/similar` | Similar/competitor apps |
| GET | `/search?q=keyword` | Search Google Play |
| GET | `/trending` | Top free/paid/grossing charts |
| GET | `/health` | Server health (no auth needed) |
| GET | `/docs` | API documentation |

### App Details
```bash
curl https://your-app.replit.app/apps/com.spotify.music \
  -H "Authorization: Bearer demo-key-123"
```

### Reviews
```bash
curl "https://your-app.replit.app/apps/com.spotify.music/reviews?count=10&sort=newest" \
  -H "Authorization: Bearer demo-key-123"
```

### Similar Apps
```bash
curl https://your-app.replit.app/apps/com.spotify.music/similar \
  -H "Authorization: Bearer demo-key-123"
```

### Search
```bash
curl "https://your-app.replit.app/search?q=music+player&n=20" \
  -H "Authorization: Bearer demo-key-123"
```

### Trending
```bash
curl "https://your-app.replit.app/trending?collection=top_free&category=MUSIC_AND_AUDIO" \
  -H "Authorization: Bearer demo-key-123"
```

## Pricing

| Plan | Price | Requests/day | Burst |
|------|-------|-------------|-------|
| Free | $0/mo | 100 | 1 req/sec |
| Starter | $19/mo | 10,000 | 1 req/sec |
| Growth | $49/mo | 50,000 | 5 req/sec |

## Setup & Running Locally

```bash
# 1. Clone
git clone https://github.com/Gabangxa/playdataapi
cd playdataapi

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set env vars
cp .env.example .env
# Edit .env if needed

# 4. Run
VALID_API_KEYS=demo-key-123,test-key-456 python app.py
# Server starts at http://localhost:3000
```

### Replit Deployment

Import the GitHub repo at [replit.com/new](https://replit.com/new), click **Run**. No config needed — Replit sets `PORT` automatically.

## Authentication

All endpoints except `/health` require:
```
Authorization: Bearer <your-api-key>
```

Default demo key: `demo-key-123` (100 req/day)

## Error Codes

| HTTP | Code | Meaning |
|------|------|---------|
| 400 | `invalid_param` | Missing/invalid query parameter |
| 401 | `auth_required` | Missing/invalid API key |
| 404 | `app_not_found` | Package ID not on Google Play |
| 429 | `rate_limit` | Rate limit exceeded |
| 502 | `upstream_error` | Google Play fetch failed |
