import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from playwright.async_api import async_playwright

COOKIES_FILE = 'cookies.json'
if '--output' in sys.argv:
    idx = sys.argv.index('--output')
    if idx + 1 < len(sys.argv):
        COOKIES_FILE = sys.argv[idx + 1]


async def main():
    print(">> Membuka browser. Login ke Twitter di jendela yang muncul.")
    print(">> Setelah login & muncul halaman Home, tutup browser ini.")
    print(">> Cookies akan otomatis tersimpan.\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
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
        page = await context.new_page()

        await page.goto('https://x.com/login', wait_until='domcontentloaded')

        print(">> Silakan login di browser...")
        print(">> Setelah halaman Home muncul, TUTUP browsernya.\n")

        try:
            await page.wait_for_url('https://x.com/home', timeout=600000)
            print(">> Login terdeteksi!")
        except Exception:
            print(">> Timeout menunggu login. Cookies tetap disimpan.")
            pass

        await asyncio.sleep(3)

        cookies = await context.cookies()
        with open(COOKIES_FILE, 'w') as f:
            json.dump(cookies, f, indent=2)
        print(f">> {len(cookies)} cookies saved ke {COOKIES_FILE}")

        await browser.close()


if __name__ == '__main__':
    asyncio.run(main())
