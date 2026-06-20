from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.helpers import _render, _session_required, _get_sid, _get_session_remaining, PROJ
from app.models import db
from config import settings as config

router = APIRouter()


@router.get('/login', response_class=HTMLResponse)
async def login_page():
    return _render('auth.html', mode='login')


@router.get('/register', response_class=HTMLResponse)
async def register_page():
    return _render('auth.html', mode='register')


@router.post('/api/register')
async def api_register(body: dict):
    username = body.get('username', '').strip()
    password = body.get('password', '')
    if not username or not password:
        return {'status': 'error', 'msg': 'Username and password required'}
    if len(password) < 4:
        return {'status': 'error', 'msg': 'Password must be at least 4 characters'}
    sid = db.register_user(username, password)
    if not sid:
        return {'status': 'error', 'msg': 'Username already taken'}
    return {'status': 'ok', 'session_id': sid, 'username': username}


@router.post('/api/login')
async def api_login(body: dict):
    username = body.get('username', '').strip()
    password = body.get('password', '')
    if not username or not password:
        return {'status': 'error', 'msg': 'Username and password required'}
    sid = db.login_user(username, password)
    if not sid:
        return {'status': 'error', 'msg': 'Invalid username or password'}
    return {'status': 'ok', 'session_id': sid, 'username': username}


@router.get('/api/verify')
async def api_verify(request: Request):
    sid = _get_sid(request)
    if not sid:
        return {'valid': False}
    valid = db.verify_session(sid)
    if not valid:
        return {'valid': False}
    user = db.get_session_user(sid)
    remaining = _get_session_remaining(sid)
    return {'valid': True, 'username': user, 'expires_in': remaining}
