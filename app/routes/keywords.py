from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.helpers import _render, _session_required, _get_sid, PROJ, _PRIORITY_RE
from app.models import db

router = APIRouter()


@router.get('/api/keywords')
async def api_keywords_list(request: Request):
    sid = _session_required(request)
    if not sid:
        return {'keywords': []}
    return {'keywords': db.get_keywords_with_priority(sid)}


@router.post('/api/keywords')
async def api_keywords_add(request: Request, body: dict):
    sid = _session_required(request)
    if not sid:
        return {'status': 'error', 'msg': 'not authenticated'}
    new_kws = body.get('keywords', [])
    if not new_kws:
        return {'status': 'error', 'msg': 'No keywords provided'}
    priority = body.get('priority')
    if priority is not None:
        added = db.add_keywords(sid, new_kws, priority=priority)
    else:
        added = []
        for kw in new_kws:
            p = 1 if _PRIORITY_RE.search(kw) else 0
            result = db.add_keywords(sid, [kw], priority=p)
            added.extend(result)
    return {'status': 'ok', 'added': added}


@router.delete('/api/keywords')
async def api_keywords_delete(request: Request, body: dict):
    sid = _session_required(request)
    if not sid:
        return {'status': 'error', 'msg': 'not authenticated'}
    remove = body.get('keywords', [])
    if not remove:
        return {'status': 'error', 'msg': 'No keywords provided'}
    db.delete_keywords(sid, remove)
    return {'status': 'ok', 'deleted': len(remove)}


@router.patch('/api/keywords/priority')
async def api_keywords_priority(request: Request, body: dict):
    sid = _session_required(request)
    if not sid:
        return {'status': 'error', 'msg': 'not authenticated'}
    keyword = body.get('keyword', '').strip().lower()
    priority = body.get('priority', 0)
    if not keyword:
        return {'status': 'error', 'msg': 'No keyword provided'}
    db.update_keyword_priority(sid, keyword, priority)
    return {'status': 'ok'}
