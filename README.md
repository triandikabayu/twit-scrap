<div align="center">

# twit-scrap

**X/Twitter Scraper & Character Analysis for Event Merchandise**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Playwright](https://img.shields.io/badge/Playwright-45ba4b?logo=playwright&logoColor=white)](https://playwright.dev)

[🇮🇩 *Baca dalam Bahasa Indonesia*](README.id.md)

---

</div>

A web application for scraping tweets from X (Twitter) to find merchandise listings from events like Comifuro, Comic Frontier, and similar conventions. Built with FastAPI and Playwright, featuring real-time streaming via SSE, multi-user session isolation, and character-level market analysis.

## Features

- **🔍 Keyword-Based Scraping** — Define priority search terms and character names; the scraper runs standalone queries plus cross-product combinations automatically.
- **⚡ Real-Time Feed** — Live tweet stream via Server-Sent Events while scraping is in progress.
- **📊 Character Analysis** — Extract mentioned characters from ISO/WTB tweets with urgency scoring and trend visualization.
- **🔐 Multi-User Sessions** — Each user has isolated data with username/password authentication.
- **👥 Multi-Account Support** — Manage multiple Twitter accounts for scraping to distribute rate limits.
- **📁 Data Export** — Download scraped tweets as CSV for external analysis.

## Quick Start

```bash
pip install -r requirements.txt
playwright install chromium
```

### 1. Authenticate with X

Opens a browser window for manual login:

```bash
python scripts/get_cookies.py
```

Cookies are saved to `cookies.json` after successful login. For multiple accounts, use `--output cookies_N.json`.

### 2. Start the Web App

```bash
python app/main.py
```

Open `http://localhost:8000`, register an account, add keywords, and start scraping.

### 3. Run a Scrape

1. Go to **Keywords** → add your search terms. Priority keywords (e.g., `#wtb cf22`) run as standalone queries and are combined with non-priority character names.
2. Go to **Scraper** → select an account → click **Start Scraping**.
3. Results stream in real time and are saved to `data/comifuro_tweets.csv` + `.json`, then imported into SQLite.

### 4. Generate Analytics

```bash
python scripts/analyze.py
```

Outputs charts to the `output/` directory.

## Architecture

```
app/
├── main.py              # FastAPI entrypoint
├── helpers.py           # Session management, Jinja2 rendering
├── state.py             # SSE broadcast state
├── routes/              # API route modules
├── models/db.py         # SQLite (WAL mode) at data/cf_scraper.db
├── data/
│   ├── characters.py    # ~40+ fandom character database
│   └── fandoms.py       # Local + Wikipedia fallback
├── static/style.css
└── templates/           # Jinja2 HTML templates
config/
├── settings.py          # Configuration (env-based credentials, date range)
└── .env.example
scripts/
├── scraper.py           # Playwright headless scraper
├── get_cookies.py       # Browser login → cookie extraction
└── analyze.py           # Chart generation
keys.py                  # twikit monkey patches for X.com compatibility
```

## Data Flow

```
User adds keywords (Web UI)
       ↓
API generates keywords.txt (priority + cross-product combos)
       ↓
Scraper subprocess (Playwright on x.com/search)
       ↓
Results → data/comifuro_tweets.csv + .json → SQLite import
       ↓
Real-time feed via SSE → Web UI
       ↓
Character analysis & charts
```

## Security

- Credentials are loaded from environment variables, never hardcoded.
- Session IDs are stored in HTTP-only cookies, not exposed in URLs.
- `.gitignore` covers `*.db`, `*.csv`, `*.json`, and `cookies.json` — no secrets in version control.
- Each user's data is fully isolated by session ID.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.10+, FastAPI, Uvicorn |
| Database | SQLite (WAL mode) |
| Scraping | Playwright (headless Chromium) |
| Frontend | Jinja2 templates, Chart.js |
| Analysis | Pandas, Matplotlib, Seaborn |

## Deployment

Designed for local deployment behind a Cloudflare Tunnel. Not compatible with serverless platforms (Vercel, Railway) due to Playwright and background process requirements.

```bash
# Example: expose via Cloudflare Tunnel
cloudflared tunnel --url http://localhost:8000
```

---

<div align="center">
  <sub>Built with Python · FastAPI · Playwright</sub>
</div>
