import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from browser_cookie3 import chrome as chrome_cookies

COOKIES_FILE = 'cookies.json'
if '--output' in sys.argv:
    idx = sys.argv.index('--output')
    if idx + 1 < len(sys.argv):
        COOKIES_FILE = sys.argv[idx + 1]

X_COOKIE_NAMES = {'auth_token', 'ct0', 'twid', 'lang', 'session_id'}


def open_chrome(url):
    """Buka Chrome — cross platform (macOS, Windows, Linux)."""
    if sys.platform == 'darwin':
        path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
        if os.path.exists(path):
            subprocess.Popen([path, url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
        subprocess.Popen(['open', '-a', 'Google Chrome', url])
    elif sys.platform == 'win32':
        candidates = [
            os.path.expandvars(r'%ProgramFiles%\Google\Chrome\Application\chrome.exe'),
            os.path.expandvars(r'%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe'),
            os.path.expandvars(r'%LocalAppData%\Google\Chrome\Application\chrome.exe'),
        ]
        for path in candidates:
            if path and os.path.exists(path):
                subprocess.Popen([path, url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return
        subprocess.Popen(['start', 'chrome', url], shell=True)
    else:
        candidates = ['google-chrome', 'chromium-browser', 'chromium']
        for bin in candidates:
            try:
                subprocess.Popen([bin, url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return
            except FileNotFoundError:
                continue


def check_auth_cookies():
    try:
        cj = chrome_cookies(domain_name='x.com')
        cookies = []
        for c in cj:
            cookies.append({
                'name': c.name,
                'value': c.value,
                'domain': c.domain,
                'path': c.path,
                'secure': bool(c.secure),
                'httpOnly': True,
                'sameSite': 'Lax',
            })
        has_auth = any(c['name'] in X_COOKIE_NAMES for c in cookies)
        return has_auth, cookies
    except Exception as e:
        return False, []


def save_cookies(cookies):
    with open(COOKIES_FILE, 'w') as f:
        json.dump(cookies, f, indent=2)
    auth_names = [c['name'] for c in cookies if c['name'] in X_COOKIE_NAMES]
    print(f"\n>> {len(cookies)} cookies saved ke {COOKIES_FILE}")
    if auth_names:
        print(f">> Auth cookies: {', '.join(auth_names)}")
    else:
        print(">> Peringatan: tidak ada auth_token. Pastikan sudah login ke X.com di Chrome.")


def main():
    print("=" * 60)
    print("  X.com Cookie Extractor")
    print("=" * 60)
    print("\nCara:")
    print("  1. Login ke X.com di Chrome ASLI lo (bukan Playwright)")
    print("  2. Pastikan halaman Home X.com sudah kebuka")
    print("  3. Kembali ke terminal ini, tekan ENTER")
    print("\n  Chrome akan dibukain otomatis...\n")

    had_auth, _ = check_auth_cookies()
    if had_auth:
        print(">> Kok udah login di Chrome sih, langsung ambil cookies aja.")
        _, cookies = check_auth_cookies()
        save_cookies(cookies)
        return

    open_chrome('https://x.com/home')

    input(">> Udah login? Tekan ENTER setelah halaman Home X.com muncul...\n")

    # Coba berkali-kali sampe dapet auth cookies
    for attempt in range(10):
        has_auth, cookies = check_auth_cookies()
        if has_auth and cookies:
            save_cookies(cookies)
            return
        if attempt < 9:
            print(f">> Cookies auth belum muncul, coba lagi ({attempt + 1}/10)...")
            time.sleep(2)

    # Terakhir: save aja apapun yang ada
    _, cookies = check_auth_cookies()
    if cookies:
        save_cookies(cookies)
    else:
        print(">> Gagal: gak dapet cookies sama sekali dari Chrome.")
        sys.exit(1)


if __name__ == '__main__':
    main()
