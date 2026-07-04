import argparse
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from browser_cookie3 import chrome as chrome_cookies

LOGIN_URL = 'https://x.com/i/jf/onboarding/web?mode=login'
HOME_URL = 'https://x.com/home'
AUTH_COOKIE_NAMES = {'auth_token', 'ct0', 'twid'}
POLL_INTERVAL = 3
TIMEOUT = 120


def get_x_cookies():
    cj = chrome_cookies(domain_name='x.com')
    return [{
        'name': c.name,
        'value': c.value,
        'domain': c.domain,
        'path': c.path,
        'secure': bool(c.secure),
        'httpOnly': True,
        'sameSite': 'Lax',
    } for c in cj]


def has_auth(cookies):
    return any(c['name'] in AUTH_COOKIE_NAMES for c in cookies)


def open_chrome(url):
    chrome = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    if os.path.exists(chrome):
        subprocess.Popen([chrome, url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.Popen(['open', '-a', 'Google Chrome', url])


def save(output_path, cookies):
    with open(output_path, 'w') as f:
        json.dump(cookies, f, indent=2)
    auth_names = [c['name'] for c in cookies if c['name'] in AUTH_COOKIE_NAMES]
    print('STATUS:ok')
    print(f'COOKIES_SAVED:{output_path}')
    if auth_names:
        print(f'MSG:Auth cookies: {", ".join(auth_names)}')


def main():
    parser = argparse.ArgumentParser(description='X.com cookie capture via real Chrome')
    parser.add_argument('--output', required=True, help='Path to save cookie JSON file')
    parser.add_argument('--username', help='(ignored — login manually in Chrome)')
    parser.add_argument('--password', help='(ignored — login manually in Chrome)')
    parser.add_argument('--email', help='(ignored — login manually in Chrome)')
    parser.add_argument('--headless', action='store_true', help='(ignored)')
    args = parser.parse_args()

    # Always open Chrome so user can log in as the correct account
    open_chrome(LOGIN_URL)
    print('MSG:Chrome opened to X.com login. Log in manually — cookies will be saved automatically.')

    start = time.time()
    while time.time() - start < TIMEOUT:
        time.sleep(POLL_INTERVAL)
        cookies = get_x_cookies()
        if has_auth(cookies):
            save(args.output, cookies)
            return

    # Fallback: save whatever we got (guest cookies)
    cookies = get_x_cookies()
    if cookies:
        with open(args.output, 'w') as f:
            json.dump(cookies, f, indent=2)
        print('STATUS:error')
        print(f'MSG:Timeout — no auth cookies found after {TIMEOUT}s. Guest-only cookies saved.')
    else:
        print('STATUS:error')
        print('MSG:No cookies could be retrieved from Chrome.')


if __name__ == '__main__':
    main()
