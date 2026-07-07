import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

COOKIES_FILE = 'cookies.json'
if '--output' in sys.argv:
    idx = sys.argv.index('--output')
    if idx + 1 < len(sys.argv):
        COOKIES_FILE = sys.argv[idx + 1]

X_COOKIE_NAMES = {'auth_token', 'ct0', 'twid', 'lang', 'session_id'}
AUTH_COOKIE_NAMES = {'auth_token', 'ct0', 'twid'}


def get_x_cookies(page):
    cookies = page.context.cookies()
    return [{
        'name': c['name'],
        'value': c['value'],
        'domain': c.get('domain', '.x.com'),
        'path': c.get('path', '/'),
        'secure': c.get('secure', True),
        'httpOnly': c.get('httpOnly', True),
        'sameSite': c.get('sameSite', 'Lax'),
    } for c in cookies]


def has_auth(cookies):
    return any(c['name'] in AUTH_COOKIE_NAMES for c in cookies)


def save_cookies(cookies):
    with open(COOKIES_FILE, 'w') as f:
        json.dump(cookies, f, indent=2)
    auth_names = [c['name'] for c in cookies if c['name'] in X_COOKIE_NAMES]
    print(f"\n>> {len(cookies)} cookies saved ke {COOKIES_FILE}")
    if auth_names:
        print(f">> Auth cookies: {', '.join(auth_names)}")
    else:
        print(">> Peringatan: tidak ada auth_token. Pastikan sudah login ke X.com.")


def _find_chrome():
    if sys.platform == 'darwin':
        path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
        return path if os.path.exists(path) else None
    elif sys.platform == 'win32':
        candidates = [
            os.path.expandvars(r'%ProgramFiles%\Google\Chrome\Application\chrome.exe'),
            os.path.expandvars(r'%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe'),
            os.path.expandvars(r'%LocalAppData%\Google\Chrome\Application\chrome.exe'),
        ]
        for p in candidates:
            if p and os.path.exists(p):
                return p
        return None
    else:
        import shutil
        for bin in ('google-chrome', 'chromium-browser', 'chromium',
                     '/usr/bin/google-chrome', '/usr/bin/chromium-browser'):
            if os.path.exists(bin) or shutil.which(bin):
                return bin
        return None


def main():
    from playwright.sync_api import sync_playwright

    print("=" * 60)
    print("  X.com Cookie Extractor")
    print("=" * 60)
    print("\nCara:")
    print("  1. Login ke X.com di browser yang terbuka")
    print("  2. Kembali ke terminal ini, tekan ENTER")
    print("\n  Browser akan dibukain otomatis...\n")

    chrome_path = _find_chrome()
    launch_kwargs = {'headless': False}
    if chrome_path:
        launch_kwargs['executable_path'] = chrome_path

    with sync_playwright() as p:
        browser = p.chromium.launch(**launch_kwargs)
        page = browser.new_page()
        page.goto('https://x.com/home')
        page.wait_for_load_state('networkidle')

        cookies = get_x_cookies(page)
        if has_auth(cookies):
            browser.close()
            save_cookies(cookies)
            return

        input(">> Udah login? Tekan ENTER setelah halaman Home X.com muncul...\n")

        for attempt in range(10):
            cookies = get_x_cookies(page)
            if has_auth(cookies):
                browser.close()
                save_cookies(cookies)
                return
            if attempt < 9:
                print(f">> Cookies auth belum muncul, coba lagi ({attempt + 1}/10)...")
                time.sleep(2)

        cookies = get_x_cookies(page)
        browser.close()
        if cookies:
            save_cookies(cookies)
        else:
            print(">> Gagal: gak dapet cookies sama sekali.")
            sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f">> Error: {e}")
        sys.exit(1)
