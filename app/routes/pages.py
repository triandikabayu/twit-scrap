from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.helpers import _render, _session_required, PROJ
from app.models import db

router = APIRouter()


@router.get('/', response_class=HTMLResponse)
async def dashboard(request: Request):
    sid = _session_required(request)
    if not sid:
        return RedirectResponse(url='/login')
    user = db.get_session_user(sid)
    return _render('dashboard.html', active='dashboard', session_id=sid, username=user)


@router.get('/scraper', response_class=HTMLResponse)
async def scraper_page(request: Request):
    sid = _session_required(request)
    if not sid:
        return RedirectResponse(url='/login')
    user = db.get_session_user(sid)
    return _render('scraper.html', active='scraper', session_id=sid, username=user)


@router.get('/analysis', response_class=HTMLResponse)
async def analysis_page(request: Request):
    sid = _session_required(request)
    if not sid:
        return RedirectResponse(url='/login')
    user = db.get_session_user(sid)
    return _render('analysis.html', active='analysis', session_id=sid, username=user)


@router.get('/data', response_class=HTMLResponse)
async def data_page(request: Request):
    sid = _session_required(request)
    if not sid:
        return RedirectResponse(url='/login')
    user = db.get_session_user(sid)
    return _render('data.html', active='data', session_id=sid, username=user)


@router.get('/keywords', response_class=HTMLResponse)
async def keywords_page(request: Request):
    sid = _session_required(request)
    if not sid:
        return RedirectResponse(url='/login')
    user = db.get_session_user(sid)
    return _render('keywords.html', active='keywords', session_id=sid, username=user)


@router.get('/accounts', response_class=HTMLResponse)
async def accounts_page(request: Request):
    sid = _session_required(request)
    if not sid:
        return RedirectResponse(url='/login')
    user = db.get_session_user(sid)
    return _render('accounts.html', active='accounts', session_id=sid, username=user)


@router.get('/manage', response_class=HTMLResponse)
async def manage_page(request: Request):
    sid = _session_required(request)
    if not sid:
        return RedirectResponse(url='/login')
    user = db.get_session_user(sid)
    return _render('manage.html', active='manage', session_id=sid, username=user)
