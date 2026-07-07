import asyncio
import concurrent.futures
import json
import os
import sys
import time as time_module

from fastapi import APIRouter, Request, Query

from app.helpers import _session_required, PROJ
from app.models import db

router = APIRouter()

# ponytail: standalone script pair in scripts/ duplicates _find_chrome.
# Acceptable — each script must work without importing app.
AUTH_COOKIE_NAMES = {'auth_token', 'ct0', 'twid'}
POLL_INTERVAL = 3
TIMEOUT = 120
LOGIN_URL = 'https://x.com/i/jf/onboarding/web?mode=login'

_thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)


def _find_chrome() -> str | None:
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
    # ponytail: Linux — explicit paths only. If not found, bundled Chromium is fine.
    for bin in ('/usr/bin/google-chrome', '/usr/bin/chromium-browser', '/snap/bin/chromium'):
        if os.path.exists(bin):
            return bin
    return None


def _capture_cookies(output_path: str) -> str | None:
    """Run Playwright synchronously in a worker thread (bypasses Windows event-loop issues)."""
    from playwright.sync_api import sync_playwright

    chrome_path = _find_chrome()
    launch_kwargs = {'headless': False}
    if chrome_path:
        launch_kwargs['executable_path'] = chrome_path

    with sync_playwright() as p:
        browser = p.chromium.launch(**launch_kwargs)
        page = browser.new_page()
        page.goto(LOGIN_URL, wait_until='networkidle')

        start = time_module.time()
        while time_module.time() - start < TIMEOUT:
            time_module.sleep(POLL_INTERVAL)
            cookies = page.context.cookies()
            has_auth = any(c['name'] in AUTH_COOKIE_NAMES for c in cookies)
            if has_auth:
                with open(output_path, 'w') as f:
                    json.dump(cookies, f, indent=2)
                browser.close()
                return output_path

        browser.close()
        return None


@router.get('/api/accounts')
async def api_accounts_list(request: Request):
    sid = _session_required(request)
    if not sid:
        return {'accounts': []}
    return {'accounts': db.get_twitter_accounts()}


@router.post('/api/accounts')
async def api_accounts_add(request: Request, body: dict):
    sid = _session_required(request)
    if not sid:
        return {'status': 'error', 'msg': 'not authenticated'}
    name = body.get('name', '').strip()
    email = body.get('email', '').strip()
    username = body.get('username', '').strip()
    password = body.get('password', '')
    if not name or not username:
        return {'status': 'error', 'msg': 'Name and username required'}
    aid = db.add_twitter_account(name, email, username, password)
    if not aid:
        return {'status': 'error', 'msg': 'Failed to add account'}
    return {'status': 'ok', 'id': aid}


@router.delete('/api/accounts/{account_id}')
async def api_accounts_delete(request: Request, account_id: int):
    sid = _session_required(request)
    if not sid:
        return {'status': 'error', 'msg': 'not authenticated'}
    ok = db.delete_twitter_account(account_id)
    return {'status': 'ok' if ok else 'error'}


@router.post('/api/accounts/{account_id}/cookies')
async def api_accounts_gen_cookies(request: Request, account_id: int, force: int = Query(0)):
    sid = _session_required(request)
    if not sid:
        return {'status': 'error', 'msg': 'not authenticated'}
    account = db.get_twitter_account(account_id)
    if not account:
        return {'status': 'error', 'msg': 'Account not found'}
    client_host = request.client.host if request.client else '0.0.0.0'
    is_remote = client_host not in ('127.0.0.1', '::1', 'localhost')
    cookies_file = f'cookies_{account_id}.json'
    if is_remote and not force:
        return {
            'status': 'remote',
            'msg': 'Koneksi dari perangkat lain terdeteksi. Browser akan terbuka di SERVER (mesin tempat server berjalan).',
            'cookies_file': cookies_file,
            'command': f'python scripts/get_cookies.py --output {cookies_file}',
        }

    username = account.get('username', '').strip()
    password = account.get('password', '').strip()
    if not username or not password:
        return {
            'status': 'error',
            'msg': 'Account has no credentials stored. Edit account or use manual method.',
            'command': f'python scripts/get_cookies.py --output {cookies_file}',
        }

    try:
        output_path = str(PROJ / cookies_file)
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(_thread_pool, _capture_cookies, output_path)

        if result:
            db.update_account_cookies(account_id, cookies_file)
            return {'status': 'ok', 'cookies_file': cookies_file}
        else:
            return {
                'status': 'error',
                'msg': f'Timeout — no auth cookies found after {TIMEOUT}s. Pastikan sudah login ke X.com.',
                'command': f'python scripts/get_cookies.py --output {cookies_file}',
            }

    except Exception as e:
        msg = str(e) or 'Unknown error (no message)'
        return {
            'status': 'error',
            'msg': msg,
            'command': f'python scripts/get_cookies.py --output {cookies_file}',
        }
