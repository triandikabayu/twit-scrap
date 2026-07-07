import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

LOGIN_URL = 'https://x.com/i/jf/onboarding/web?mode=login'
AUTH_COOKIE_NAMES = {'auth_token', 'ct0', 'twid'}
POLL_INTERVAL = 3
TIMEOUT = 120


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


def save(output_path, cookies):
    with open(output_path, 'w') as f:
        json.dump(cookies, f, indent=2)
    auth_names = [c['name'] for c in cookies if c['name'] in AUTH_COOKIE_NAMES]
    print('STATUS:ok')
    print(f'COOKIES_SAVED:{output_path}')
    if auth_names:
        print(f'MSG:Auth cookies: {", ".join(auth_names)}')


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
    for bin in ('/usr/bin/google-chrome', '/usr/bin/chromium-browser', '/snap/bin/chromium'):
        if os.path.exists(bin):
            return bin
    return None


def main():
    parser = argparse.ArgumentParser(description='X.com cookie capture via Playwright')
    parser.add_argument('--output', required=True, help='Path to save cookie JSON file')
    parser.add_argument('--username', help='(ignored — login manually)')
    parser.add_argument('--password', help='(ignored — login manually)')
    parser.add_argument('--email', help='(ignored — login manually)')
    parser.add_argument('--headless', action='store_true', help='(ignored)')
    args = parser.parse_args()

    from playwright.sync_api import sync_playwright

    chrome_path = _find_chrome()
    launch_kwargs = {'headless': False}
    if chrome_path:
        launch_kwargs['executable_path'] = chrome_path

    with sync_playwright() as p:
        browser = p.chromium.launch(**launch_kwargs)
        page = browser.new_page()
        page.goto(LOGIN_URL)
        page.wait_for_load_state('networkidle')

        print('MSG:Chrome opened to X.com login. Log in manually — cookies will be saved automatically.')

        start = time.time()
        while time.time() - start < TIMEOUT:
            time.sleep(POLL_INTERVAL)
            cookies = get_x_cookies(page)
            if has_auth(cookies):
                browser.close()
                save(args.output, cookies)
                return

        browser.close()
        print('STATUS:error')
        print(f'MSG:Timeout — no auth cookies found after {TIMEOUT}s. Pastikan sudah login ke X.com.')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('STATUS:error')
        print(f'MSG:Error: {e}')
        sys.exit(1)
