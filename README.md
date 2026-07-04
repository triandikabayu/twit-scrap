<div align="center">

# twit-scrap

**X/Twitter Scraper — Extract tweets using your own account, securely stored in a local database**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Playwright](https://img.shields.io/badge/Playwright-45ba4b?logo=playwright&logoColor=white)](https://playwright.dev)

[🇮🇩 *Baca dalam Bahasa Indonesia*](README.id.md)

---

</div>

A web application for scraping tweets from X (Twitter) by utilizing your own Twitter account credentials. Built with FastAPI and Playwright, it provides real-time streaming via SSE, multi-user session isolation, and character-level analysis. All scraped data is stored securely in a local SQLite database — no external servers involved, your data remains under your control.

## Features

- **🔍 Keyword-Based Scraping** — Define priority search terms and character names; the scraper runs standalone queries plus cross-product combinations automatically.
- **⚡ Real-Time Feed** — Live tweet stream via Server-Sent Events while scraping is in progress.
- **📊 Character Extraction** — Automatically identifies and extracts character names from tweets with frequency scoring and trend visualization.
- **🔐 Multi-User Sessions** — Each user has isolated data with username/password authentication.
- **👥 Multi-Account Support** — Manage multiple Twitter accounts to distribute scraping load and avoid rate limits.
- **📁 Data Export** — Download scraped tweets as CSV for external analysis.

## Running the App

### 0. Setup

```bash
pip install -r requirements.txt
playwright install chromium
```

### 1. Authenticate Twitter Accounts

Open a browser to log into X manually — cookies are saved for headless scraping later.

**Single account:**
```bash
python scripts/get_cookies.py
```

**Multiple accounts (distributes rate limits):**
```bash
python scripts/get_cookies.py --output cookies_1.json
python scripts/get_cookies.py --output cookies_2.json
```

Each command opens a browser window — log in, wait for the home page to load, then close the browser.

---

### 2. Start the Web App

```bash
python app/main.py
```

Open **`http://localhost:8000`** in your browser.

---

### 3. Register & Login

On first visit, you'll be redirected to `/login`. Click **Register**, enter a username and password, then log in. Your data (keywords, tweets, accounts) is isolated per user.

---

### 4. Add Twitter Accounts

Navigate to **Accounts** → click **Add Account** → fill in the Twitter email/username/password.

- The first account is created automatically from your `TWITTER_*` environment variables.
- Each account can **Generate Cookies** from the accounts list — this runs `get_cookies.py` for that account.
- Use different accounts for scraping to avoid rate limits.

---

### 5. Add Keywords

Navigate to **Keywords**:

| Field | Description |
|-------|-------------|
| **Priority keyword** | Main search query (e.g., `#wtb cf22`, `#wtb comifuro`, `cari cf`). These run standalone **and** are combined with every non-priority keyword. |
| **Non-priority keyword** | Character or item names (e.g., `Hoshino Ruby`, `Miyabi`, `figure`, `acrylic stand`). These run as standalone queries too. |
| **Fandom Search** | Type a fandom name → auto-suggests characters from the local database. Selected characters become non-priority keywords. |

Mark priority keywords with a ⭐ toggle — they'll be cross-product combined with all non-priority keywords during scraping.

---

### 6. Run a Scrape

Navigate to **Scraper**:

1. **Select an account** from the dropdown (uses its cookies for authentication).
2. **Select which keywords** to scrape (checkboxes).
3. Click **Start Scraping**.

The scraper runs as a background process — you can navigate away and the progress bar + live tweet feed will follow you via the persistent banner at the top.

**What happens:**
- The API generates a `keywords.txt` containing every selected keyword as a standalone query, plus `{priority} {non-priority}` combinations.
- Playwright opens `x.com/search` with each query, scrolls, and extracts tweet text.
- Tweets stream to the UI via **Server-Sent Events** — no page refresh needed.
- Results are saved to `data/comifuro_tweets.csv` + `.json`, then imported into SQLite.

**Stop** at any time with the Stop button. Resume later — only new tweets are imported.

---

### 7. View & Manage Data

Navigate to **Data** → browse scraped tweets in a paginated table with keyword and character filters.

Navigate to **Manage** → see tweet counts grouped by keyword. Delete tweets by keyword, character name, or wipe everything.

---

### 8. Generate Analytics (CLI)

```bash
python scripts/analyze.py
```

Produces charts (keyword frequency, character mentions, urgency scoring) in the `output/` directory.

---

## End-to-End Flow Summary

```
[Setup]           pip install + playwright install
     ↓
[Cookies]         get_cookies.py → cookies.json
     ↓
[Web App]         python app/main.py → localhost:8000
     ↓
[Register]        create user account
     ↓
[Accounts]        add Twitter accounts (email/password)
     ↓
[Keywords]        add priority + character keywords
     ↓
[Scraper]         select account → select keywords → start
     ↓
[Live Feed]       SSE streams tweets in real time
     ↓
[Data/Manage]     browse, filter, delete tweets
     ↓
[Analyze]         python scripts/analyze.py → charts
```

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
