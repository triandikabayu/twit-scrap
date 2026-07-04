<div align="center">

# twit-scrap

**X/Twitter Scraper & Analisis Karakter untuk Event Merchandise**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Playwright](https://img.shields.io/badge/Playwright-45ba4b?logo=playwright&logoColor=white)](https://playwright.dev)

[🇬🇧 *Read in English*](README.md)

---

</div>

Aplikasi web untuk scraping tweet dari X (Twitter) guna mencari listing merchandise dari event seperti Comifuro, Comic Frontier, dan konvensi serupa. Dibangun dengan FastAPI dan Playwright, dilengkapi streaming real-time via SSE, isolasi sesi multi-user, serta analisis karakter level pasar.

## Fitur

- **🔍 Scraping Berbasis Keyword** — Tentukan kata kunci prioritas dan nama karakter; scraper otomatis menjalankan query standalone plus kombinasi cross-product.
- **⚡ Feed Real-Time** — Live stream tweet via Server-Sent Events selama proses scraping berlangsung.
- **📊 Analisis Karakter** — Ekstraksi karakter yang disebut dalam tweet ISO/WTB dengan skoring urgensi dan visualisasi tren.
- **🔐 Sesi Multi-User** — Setiap pengguna memiliki data terisolasi dengan autentikasi username/password.
- **👥 Dukungan Multi-Akun** — Kelola banyak akun Twitter untuk scraping guna mendistribusikan batas rate limit.
- **📁 Ekspor Data** — Unduh hasil scraping sebagai CSV untuk analisis eksternal.

## Memulai

```bash
pip install -r requirements.txt
playwright install chromium
```

### 1. Autentikasi ke X

Membuka jendela browser untuk login manual:

```bash
python scripts/get_cookies.py
```

Cookie akan tersimpan ke `cookies.json` setelah login berhasil. Untuk banyak akun, gunakan `--output cookies_N.json`.

### 2. Jalankan Web App

```bash
python app/main.py
```

Buka `http://localhost:8000`, daftar akun, tambah keyword, dan mulai scraping.

### 3. Mulai Scrape

1. Buka halaman **Keywords** → tambah kata kunci. Keyword prioritas (misal `#wtb cf22`) dijalankan sebagai query standalone dan dikombinasikan dengan nama karakter non-prioritas.
2. Buka halaman **Scraper** → pilih akun → klik **Start Scraping**.
3. Hasil mengalir real-time dan tersimpan ke `data/comifuro_tweets.csv` + `.json`, lalu diimpor ke SQLite.

### 4. Generate Analitik

```bash
python scripts/analyze.py
```

Menghasilkan grafik ke direktori `output/`.

## Arsitektur

```
app/
├── main.py              # Entrypoint FastAPI
├── helpers.py           # Manajemen sesi, rendering Jinja2
├── state.py             # State broadcast SSE
├── routes/              # Modul route API
├── models/db.py         # SQLite (WAL mode) di data/cf_scraper.db
├── data/
│   ├── characters.py    # Database ~40+ fandom karakter
│   └── fandoms.py       # Fallback lokal + Wikipedia
├── static/style.css
└── templates/           # Template HTML Jinja2
config/
├── settings.py          # Konfigurasi (kredensial via env, date range)
└── .env.example
scripts/
├── scraper.py           # Scraper headless Playwright
├── get_cookies.py       # Login browser → ekstraksi cookie
└── analyze.py           # Generate grafik
keys.py                  # Monkey patch twikit untuk kompatibilitas X.com
```

## Alur Data

```
User menambah keyword (Web UI)
       ↓
API generate keywords.txt (prioritas + kombinasi cross-product)
       ↓
Subprocess scraper (Playwright di x.com/search)
       ↓
Hasil → data/comifuro_tweets.csv + .json → import SQLite
       ↓
Feed real-time via SSE → Web UI
       ↓
Analisis karakter & grafik
```

## Keamanan

- Kredensial diambil dari environment variable, tidak pernah di-hardcode.
- Session ID disimpan di HTTP cookie, tidak terekspos di URL.
- `.gitignore` mencakup `*.db`, `*.csv`, `*.json`, dan `cookies.json` — tidak ada rahasia di version control.
- Data setiap pengguna terisolasi penuh berdasarkan session ID.

## Tech Stack

| Layer | Teknologi |
|-------|-----------|
| Backend | Python 3.10+, FastAPI, Uvicorn |
| Database | SQLite (WAL mode) |
| Scraping | Playwright (headless Chromium) |
| Frontend | Jinja2 templates, Chart.js |
| Analisis | Pandas, Matplotlib, Seaborn |

## Deployment

Dirancang untuk deployment lokal di belakang Cloudflare Tunnel. Tidak kompatibel dengan platform serverless (Vercel, Railway) karena membutuhkan Playwright dan proses background.

```bash
# Contoh: expose via Cloudflare Tunnel
cloudflared tunnel --url http://localhost:8000
```

---

<div align="center">
  <sub>Dibangun dengan Python · FastAPI · Playwright</sub>
</div>
