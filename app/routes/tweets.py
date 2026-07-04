import csv
import io
from datetime import datetime

from fastapi import APIRouter, Request, Query
from fastapi.responses import JSONResponse, Response

from app.helpers import _render, _session_required, _get_sid, PROJ
from app.models import db

router = APIRouter()


@router.get('/api/stats')
async def api_stats(request: Request):
    sid = _session_required(request)
    if not sid:
        return {'error': 'not authenticated'}
    return db.get_session_stats(sid)


@router.get('/api/tweets')
async def api_tweets(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    q: str = '',
    keyword: str = '',
    char: str = '',
):
    sid = _session_required(request)
    if not sid:
        return {'error': 'not authenticated', 'tweets': [], 'total': 0, 'page': page, 'total_pages': 1}
    user_keywords = [kw['keyword'] for kw in db.get_keywords_with_priority(sid) if not kw['priority']]
    tweets, total = db.get_tweets(sid, q, keyword, char, page, limit, user_keywords=user_keywords)
    total_pages = max(1, (total + limit - 1) // limit)
    return {'tweets': tweets, 'total': total, 'page': page, 'total_pages': total_pages}


@router.delete('/api/tweets')
async def api_delete_tweets(request: Request):
    sid = _session_required(request)
    if not sid:
        return JSONResponse({'status': 'error', 'msg': 'not authenticated'}, 401)
    body = await request.json()
    keyword = body.get('keyword', '')
    char = body.get('char', '')
    deleted = db.delete_tweets(sid, keyword=keyword, char=char)
    return {'status': 'ok', 'deleted': deleted}


@router.get('/api/tweets/summary')
async def api_tweets_summary(request: Request):
    sid = _session_required(request)
    if not sid:
        return {'keywords': [], 'characters': []}
    return db.get_tweets_summary(sid)


@router.get('/api/export')
async def api_export(request: Request, q: str = '', keyword: str = '', char: str = ''):
    sid = _session_required(request)
    if not sid:
        return Response('not authenticated', status=401)
    user_keywords = [kw['keyword'] for kw in db.get_keywords_with_priority(sid) if not kw['priority']]
    tweets, _ = db.get_tweets(sid, q, keyword, char, 1, 999999, user_keywords=user_keywords)
    output = io.StringIO()
    if tweets:
        fieldnames = ['full_text', 'user_screen_name', 'tweet_date', 'keyword', 'url', 'favorite_count', 'retweet_count']
        w = csv.DictWriter(output, fieldnames=fieldnames)
        w.writeheader()
        for t in tweets:
            w.writerow({k: t.get(k, '') for k in fieldnames})
    return Response(
        content=output.getvalue(),
        media_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename=cf_tweets_{datetime.now():%Y%m%d_%H%M%S}.csv'},
    )
