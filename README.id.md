<div align="center">

# twit-scrap

**X/Twitter Scraper — Ekstrak tweet menggunakan akun Anda, tersimpan aman di database lokal**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Playwright](https://img.shields.io/badge/Playwright-45ba4b?logo=playwright&logoColor=white)](https://playwright.dev)

[🇬🇧 *Read in English*](README.md)

---

</div>

Aplikasi web untuk scraping tweet dari X (Twitter) menggunakan kredensial akun Twitter Anda sendiri. Dibangun dengan FastAPI dan Playwright, dilengkapi streaming real-time via SSE, isolasi sesi multi-user, serta analisis berbasis karakter. Seluruh data hasil scraping disimpan aman di database SQLite lokal — tanpa keterlibatan server eksternal, data Anda sepenuhnya berada dalam kendali Anda.

## Fitur

- **🔍 Scraping Berbasis Keyword** — Tentukan kata kunci prioritas dan nama karakter; scraper otomatis menjalankan query standalone plus kombinasi cross-product.
- **⚡ Feed Real-Time** — Live stream tweet via Server-Sent Events selama proses scraping berlangsung.
- **📊 Ekstraksi Karakter** — Mendeteksi dan mengekstrak nama karakter dari tweet secara otomatis dengan skoring frekuensi dan visualisasi tren.
- **🔐 Sesi Multi-User** — Setiap pengguna memiliki data terisolasi dengan autentikasi username/password.
- **👥 Dukungan Multi-Akun** — Kelola banyak akun Twitter untuk mendistribusikan beban scraping dan menghindari rate limit.
- **📁 Ekspor Data** — Unduh hasil scraping sebagai CSV untuk analisis eksternal.

## Menjalankan Aplikasi

### 0. Persiapan

```bash
pip install -r requirements.txt
playwright install chromium
```

### 1. Autentikasi Akun Twitter

Buka browser untuk login ke X secara manual — cookie disimpan untuk scraping headless nantinya.

**Satu akun:**
```bash
python scripts/get_cookies.py
```

**Banyak akun (membagi beban rate limit):**
```bash
python scripts/get_cookies.py --output cookies_1.json
python scripts/get_cookies.py --output cookies_2.json
```

Setiap perintah akan membuka jendela browser — login, tunggu halaman home muncul, lalu tutup browser.

---

### 2. Jalankan Web App

```bash
python app/main.py
```

Buka **`http://localhost:8000`** di browser.

---

### 3. Register & Login

Kunjungan pertama akan diarahkan ke `/login`. Klik **Register**, masukkan username dan password, lalu login. Data (keyword, tweet, akun) terisolasi per pengguna.

---

### 4. Tambah Akun Twitter

Navigasi ke **Accounts** → klik **Add Account** → isi email/username/password Twitter.

- Akun pertama dibuat otomatis dari environment variable `TWITTER_*`.
- Setiap akun bisa **Generate Cookies** dari daftar akun — menjalankan `get_cookies.py` untuk akun tersebut.
- Gunakan akun berbeda untuk scraping agar terhindar dari rate limit.

---

### 5. Tambah Keywords

Navigasi ke **Keywords**:

| Kolom | Deskripsi |
|-------|-----------|
| **Priority keyword** | Query utama (misal `#wtb cf22`, `#wtb comifuro`, `cari cf`). Dijalankan standalone **dan** dikombinasikan dengan setiap keyword non-priority. |
| **Non-priority keyword** | Nama karakter atau barang (misal `Hoshino Ruby`, `Miyabi`, `figure`, `acrylic stand`). Juga dijalankan sebagai query standalone. |
| **Fandom Search** | Ketik nama fandom → saran karakter dari database lokal. Karakter terpilih jadi keyword non-priority. |

Tandai keyword prioritas dengan toggle ⭐ — nanti akan di-cross-product dengan semua keyword non-priority saat scraping.

---

### 6. Jalankan Scrape

Navigasi ke **Scraper**:

1. **Pilih akun** dari dropdown (menggunakan cookie akun tersebut untuk autentikasi).
2. **Pilih keyword** yang ingin discrape (centang).
3. Klik **Start Scraping**.

Scraper berjalan sebagai proses background — kamu bisa navigasi ke halaman lain, progress bar dan live feed akan tetap terlihat di banner atas.

**Yang terjadi:**
- API membuat `keywords.txt` berisi setiap keyword terpilih sebagai query standalone, plus kombinasi `{prioritas} {non-prioritas}`.
- Playwright membuka `x.com/search` untuk setiap query, scroll, dan mengekstrak teks tweet.
- Tweet mengalir ke UI via **Server-Sent Events** — tanpa perlu refresh halaman.
- Hasil disimpan ke `data/comifuro_tweets.csv` + `.json`, lalu diimpor ke SQLite.

**Hentikan** kapan saja dengan tombol Stop. Lanjutkan nanti — hanya tweet baru yang diimpor.

---

### 7. Lihat & Kelola Data

Navigasi ke **Data** → lihat tweet dalam tabel berpaginasi dengan filter keyword dan karakter.

Navigasi ke **Manage** → lihat jumlah tweet per keyword. Hapus tweet per keyword, per nama karakter, atau hapus semua.

---

### 8. Generate Analitik (CLI)

```bash
python scripts/analyze.py
```

Menghasilkan grafik (frekuensi keyword, sebutan karakter, skor urgensi) di direktori `output/`.

---

## Ringkasan Alur End-to-End

```
[Persiapan]       pip install + playwright install
     ↓
[Cookies]         get_cookies.py → cookies.json
     ↓
[Web App]         python app/main.py → localhost:8000
     ↓
[Register]        buat akun pengguna
     ↓
[Accounts]        tambah akun Twitter (email/password)
     ↓
[Keywords]        tambah keyword prioritas + karakter
     ↓
[Scraper]         pilih akun → pilih keyword → mulai
     ↓
[Live Feed]       SSE streaming tweet real-time
     ↓
[Data/Manage]     lihat, filter, hapus tweet
     ↓
[Analyze]         python scripts/analyze.py → grafik
```

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
