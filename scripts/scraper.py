import asyncio
import csv
import json
import os
import random
import re
import sys
from datetime import datetime, timezone
from urllib.parse import quote

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from playwright.async_api import async_playwright

from config.settings import TWITTER_EMAIL, TWITTER_USERNAME, TWITTER_PASSWORD

sys.dont_write_bytecode = True

COOKIES_FILE = 'cookies.json'
if '--cookies' in sys.argv:
    idx = sys.argv.index('--cookies')
    if idx + 1 < len(sys.argv):
        COOKIES_FILE = sys.argv[idx + 1]
CSV_PATH = 'data/comifuro_tweets.csv'
JSON_PATH = 'data/comifuro_tweets.json'
DATE_FROM = datetime(2024, 1, 1)
DATE_TO = datetime(2026, 12, 31, 23, 59, 59)

CSV_HEADERS = [
    'tweet_id', 'created_at', 'date', 'month', 'hour', 'full_text', 'lang',
    'user_screen_name', 'user_name', 'user_followers',
    'favorite_count', 'retweet_count', 'reply_count', 'quote_count',
    'url', 'keyword'
]

REQUEST_DELAY = (2, 4)
SCROLL_LIMIT = 50
SCROLL_DELAY = (3, 5)
INITIAL_DELAY = 6


def load_keywords(path='keywords.txt'):
    keywords = []
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('# '):
                keywords.append(line)
    return keywords


def load_existing_ids(path):
    if not os.path.isfile(path):
        return set()
    with open(path, 'r', newline='', encoding='utf-8') as f:
        return {row['tweet_id'] for row in csv.DictReader(f)}


def init_csv(path):
    exists = os.path.isfile(path)
    f = open(path, 'a', newline='', encoding='utf-8')
    writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
    if not exists or os.path.getsize(path) == 0:
        writer.writeheader()
    return f, writer


def build_url(keyword):
    kw = keyword.strip()
    query = f'{kw} since:2024-01-01 until:2026-12-31'
    return f'https://x.com/search?q={quote(query)}&src=typed_query&f=live'


async def extract_tweet_data(article, keyword):
    try:
        tweet_link = article.locator('a[href*="/status/"]').first
        if not await tweet_link.count():
            return None
        href = await tweet_link.get_attribute('href') or ''
        parts = href.split('/status/')
        if len(parts) < 2:
            return None
        tweet_id = parts[1].split('?')[0]
        parts2 = href.split('/')
        screen_name = ''
        for i, p in enumerate(parts2):
            if p == 'status' and i > 0:
                screen_name = parts2[i - 1].replace('@', '')
                break

        text_el = article.locator('[data-testid="tweetText"]').first
        full_text = ''
        if await text_el.count():
            full_text = await text_el.inner_text()

        time_el = article.locator('time').first
        created_at = ''
        dt = None
        if await time_el.count():
            created_at = await time_el.get_attribute('datetime') or ''
            try:
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                if dt.tzinfo:
                    dt = dt.replace(tzinfo=None)
                if dt < DATE_FROM or dt > DATE_TO:
                    return None
            except Exception:
                pass

        user_name_el = article.locator('[data-testid="User-Name"]').first
        user_name = ''
        if await user_name_el.count():
            user_name = await user_name_el.inner_text()
            user_name = user_name.split('\n')[0] if user_name else ''

        fav_el = article.locator('[data-testid="like"]').first
        fav = await _parse_count(fav_el)

        rt_el = article.locator('[data-testid="retweet"]').first
        rt = await _parse_count(rt_el)

        reply_el = article.locator('[data-testid="reply"]').first
        reply = await _parse_count(reply_el)

        return {
            'tweet_id': tweet_id,
            'created_at': created_at,
            'date': dt.strftime('%Y-%m-%d') if dt else '',
            'month': dt.strftime('%Y-%m') if dt else '',
            'hour': str(dt.hour) if dt else '',
            'full_text': full_text.replace('\n', ' ').replace('\r', ' '),
            'lang': 'id',
            'user_screen_name': screen_name,
            'user_name': user_name,
            'user_followers': 0,
            'favorite_count': fav,
            'retweet_count': rt,
            'reply_count': reply,
            'quote_count': 0,
            'url': f'https://x.com/{screen_name}/status/{tweet_id}',
            'keyword': keyword
        }
    except Exception:
        return None


async def _parse_count(loc):
    if not await loc.count():
        return 0
    try:
        txt = await loc.inner_text() or '0'
        txt = txt.strip()
        if 'K' in txt or 'k' in txt:
            txt = txt.replace('K', '').replace('k', '')
            return int(float(txt) * 1000)
        txt = re.sub(r'[^\d]', '', txt)
        return int(txt) if txt else 0
    except Exception:
        return 0


async def scrape_keyword(page, keyword, writer, csv_file, existing_ids, all_tweets):
    url = build_url(keyword)
    print(f"\n[{keyword}]")

    try:
        await page.goto(url, wait_until='domcontentloaded', timeout=30000)
    except Exception as e:
        print(f"  Error loading: {e}")
        return 0

    await asyncio.sleep(INITIAL_DELAY)

    seen_ids = set()
    total_new = 0
    no_new_rounds = 0
    scroll_count = 0

    while scroll_count < SCROLL_LIMIT:
        scroll_count += 1
        articles = page.locator('article[data-testid="tweet"]')
        count = await articles.count()

        batch = 0
        for i in range(count):
            try:
                article = articles.nth(i)
                row = await extract_tweet_data(article, keyword)
                if row is None:
                    continue
                if row['tweet_id'] in existing_ids or row['tweet_id'] in seen_ids:
                    continue
                seen_ids.add(row['tweet_id'])
                writer.writerow(row)
                csv_file.flush()
                existing_ids.add(row['tweet_id'])
                all_tweets.append(row)
                print(f"TWEET_JSON:{json.dumps(row, ensure_ascii=False)}", flush=True)
                batch += 1
                total_new += 1
            except Exception:
                continue

        if batch > 0:
            print(f"  Scroll {scroll_count}: +{batch} (total {total_new})")
            no_new_rounds = 0
        else:
            no_new_rounds += 1

        if no_new_rounds >= 15:
            break

        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        await asyncio.sleep(random.uniform(*SCROLL_DELAY))

    return total_new


async def main():
    if not os.path.isfile(COOKIES_FILE):
        print(">> cookies.json tidak ditemukan!")
        print(">> Jalankan: python scripts/get_cookies.py")
        sys.exit(1)

    keywords = load_keywords()
    if not keywords:
        print(">> keywords.txt kosong!")
        sys.exit(1)

    existing_ids = load_existing_ids(CSV_PATH)
    csv_file, csv_writer = init_csv(CSV_PATH)
    all_tweets = []
    grand_total = 0

    print(f">> Keywords: {len(keywords)}, existing: {len(existing_ids)} tweets\n", flush=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 900},
            user_agent=(
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/124.0.0.0 Safari/537.36'
            )
        )

        with open(COOKIES_FILE, 'r') as f:
            raw_cookies = json.load(f)
        cookies = []
        for c in raw_cookies:
            cookie = {k: v for k, v in c.items()
                      if k in ('name', 'value', 'domain', 'path',
                               'expires', 'httpOnly', 'secure', 'sameSite')}
            ss = cookie.get('sameSite')
            if ss is None:
                cookie['sameSite'] = 'Lax'
            elif isinstance(ss, str) and ss.lower() in ('no_restriction', 'none'):
                cookie['sameSite'] = 'None'
            elif isinstance(ss, str) and ss.lower() == 'lax':
                cookie['sameSite'] = 'Lax'
            elif isinstance(ss, str) and ss.lower() == 'strict':
                cookie['sameSite'] = 'Strict'
            if 'secure' in cookie:
                cookie['secure'] = bool(cookie['secure'])
            cookies.append(cookie)
        await context.add_cookies(cookies)
        print(f">> Cookies loaded ({len(cookies)} entries)")

        page = await context.new_page()

        await page.goto('https://x.com/home', wait_until='domcontentloaded')
        await asyncio.sleep(3)

        if 'login' in page.url or 'flow' in page.url:
            print(">> Cookies expired. Dapatkan cookies baru:")
            print("   python scripts/get_cookies.py")
            await browser.close()
            sys.exit(1)

        print(">> Session valid, mulai scraping...\n")

        for kw in keywords:
            new = await scrape_keyword(
                page, kw, csv_writer, csv_file, existing_ids, all_tweets
            )
            grand_total += new
            await asyncio.sleep(random.uniform(*REQUEST_DELAY))

        await browser.close()

    csv_file.close()

    if all_tweets:
        with open(JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(all_tweets, f, ensure_ascii=False, indent=2)

    print(f"\nSELESAI! Total baru: {grand_total}")
    print(f"CSV: {CSV_PATH}")


if __name__ == '__main__':
    asyncio.run(main())
