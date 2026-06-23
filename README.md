# twit-scrap

Scrape tweets from X (Twitter) buat nyari data yg kalian pengen. FastAPI web app, pake Playwright buat scraping langsung dari x.com/search.

## Cara pake

```bash
pip install -r requirements.txt
playwright install chromium
```

### 1. Login

Buka browser buat login ke X (Twitter):

```bash
python scripts/get_cookies.py
```

Nanti browser kebuka, tinggal login manual aja. Setelah berhasil login, cookies bakal kesimpen di `cookies.json`.

### 2. Jalankan web app

```bash
python app/main.py
```

Buka `http://localhost:8000` di browser, tinggal register akun, tambah keywords, trus start scraping.

### 3. Scrape

- Buka halaman **Keywords** -> tambah keyword yang mau discrape. Yang kepriority bakal dikombinin sama keyword non-priority pas scraping.
- Buka halaman **Scraper** -> pilih keyword -> klik **Start Scraping**.
- Hasilnya ngalir realtime lewat SSE, kumpul di `data/comifuro_tweets.csv` + `.json`.

### 4. Analisis

```bash
python scripts/analyze.py
```

Bikin chart ke folder `output/`.

## Project structure

```
app/
├── main.py              # FastAPI entrypoint
├── helpers.py           # Session helper, Jinja2 render, dll
├── state.py             # SSE shared state
├── routes/              # API endpoints
├── models/db.py         # SQLite di data/cf_scraper.db
├── data/
│   ├── characters.py    # ~40+ fandom character database
│   └── fandoms.py       # Local + Wikipedia fandom fallback
├── static/style.css
└── templates/           # Jinja2 HTML templates
config/
├── settings.py          # Konfigurasi (creds, date range, dll)
└── .env.example
scripts/
├── scraper.py           # Playwright scraping
├── get_cookies.py       # Login browser -> ambil cookies
└── analyze.py           # Generate chart
keys.py                  # Monkey patches buat twikit
```

## Notes

- Pake SQLite, jadi data tiap session beda-beda.
- Scraper pake Playwright headless Chrome, scroll sampe dapet atau mentok.
- Cookie session expiry 30 menit.
- Ada multi-account support buat scraping pake banyak akun X.
- `.gitignore` udah include `*.db`, `*.csv`, `*.json`, `cookies.json` — kredensial aman.

## Tech

Python 3.10+, FastAPI, SQLite (WAL), Playwright, Jinja2, twikit (di-monkey-patch biar work), Pandas, Matplotlib.

Dijalanin lokal doang — gak bisa di-Vercel soalnya pake Playwright + background process.
