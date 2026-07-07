import asyncio
import sys
from pathlib import Path

from fastapi import APIRouter, Request, Query
from fastapi.responses import JSONResponse

from app.helpers import _render, _session_required, _get_sid, PROJ
from app.models import db

router = APIRouter()


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
        proc = await asyncio.create_subprocess_exec(
            sys.executable, str(PROJ / 'scripts' / 'auto_login.py'),
            '--username', username,
            '--password', password,
            '--output', str(PROJ / cookies_file),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=str(PROJ),
        )
        stdout_bytes, _ = await asyncio.wait_for(proc.communicate(), timeout=120)
        stdout = stdout_bytes.decode('utf-8', errors='replace')
    except asyncio.TimeoutError:
        if proc:
            proc.terminate()
        return {'status': 'error', 'msg': 'Login timed out after 120s'}
    except Exception as e:
        return {'status': 'error', 'msg': str(e) or 'Gagal menjalankan script'}

    if proc.returncode == 0 and 'STATUS:ok' in stdout:
        db.update_account_cookies(account_id, cookies_file)
        return {'status': 'ok', 'cookies_file': cookies_file}
    elif proc.returncode == 2 or 'STATUS:challenge' in stdout:
        return {
            'status': 'challenge',
            'msg': '2FA atau challenge terdeteksi. Gunakan metode manual.',
            'command': f'python scripts/get_cookies.py --output {cookies_file}',
        }
    else:
        msg = None
        for line in stdout.splitlines():
            if line.startswith('MSG:'):
                msg = line[4:]
                break
        if not msg:
            msg = 'Login gagal'
        return {
            'status': 'error',
            'msg': msg,
            'command': f'python scripts/get_cookies.py --output {cookies_file}',
        }
