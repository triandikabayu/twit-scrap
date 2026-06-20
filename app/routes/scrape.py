import asyncio
import json
import re
import os
import sys
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from app.helpers import _render, _session_required, PROJ
from app.models import db

router = APIRouter()

# SSE state
_scrape_proc: asyncio.subprocess.Process | None = None
_scrape_subscribers: list[asyncio.Queue] = []
_scrape_lock = asyncio.Lock()
_scrape_task: asyncio.Task | None = None
_scrape_stop_event = asyncio.Event()
_scrape_state = {'status': 'idle', 'current': 0, 'total': 0, 'total_new': 0, 'log': []}


async def _scrape_broadcast(event_type: str, data: dict):
    async with _scrape_lock:
        for q in _scrape_subscribers[:]:
            try:
                q.put_nowait((event_type, data))
            except asyncio.QueueFull:
                pass


async def _scrape_reader(proc: asyncio.subprocess.Process):
    global _scrape_state
    kw_total = 0
    kw_current = 0
    total_new = 0
    kw_re = re.compile(r'^\[(.+?)\]')
    scroll_re = re.compile(r'Scroll\s+\d+:\s+\+(\d+)\s+\(total\s+(\d+)\)')
    done_re = re.compile(r'SELESAI!\s+Total\s+baru:\s+(\d+)', re.IGNORECASE)
    keywords_re = re.compile(r'Keywords:\s+(\d+)')
    tweet_json_re = re.compile(r'^TWEET_JSON:(.+)')
    session_re = re.compile(r'Session\s+valid')
    error_re = re.compile(r'(Error|Gagal|tidak\s+ditemukan|expired)', re.IGNORECASE)
    _scrape_state['status'] = 'running'

    while True:
        line = await proc.stdout.readline()
        if not line:
            break
        text = line.decode('utf-8', errors='replace').strip()
        if not text:
            continue
        m = keywords_re.search(text)
        if m:
            kw_total = int(m.group(1))
            _scrape_state.update({'current': 0, 'total': kw_total, 'total_new': 0})
            await _scrape_broadcast('progress', {'current': 0, 'total': kw_total, 'total_new': 0})
        m = kw_re.search(text)
        if m:
            kw_current += 1
            _scrape_state['current'] = kw_current
            await _scrape_broadcast('progress', {'current': kw_current, 'total': kw_total or 1, 'total_new': total_new})
        m = scroll_re.search(text)
        if m:
            total_new = int(m.group(2))
            _scrape_state['total_new'] = total_new
            await _scrape_broadcast('progress', {'current': kw_current, 'total': kw_total or 1, 'total_new': total_new})
        if session_re.search(text):
            await _scrape_broadcast('log', {'msg': text, 'type': 'success'})
        m = tweet_json_re.match(text)
        if m:
            try:
                tweet_data = json.loads(m.group(1))
                await _scrape_broadcast('tweet', {
                    'text': tweet_data.get('full_text', '')[:120],
                    'user': tweet_data.get('user_screen_name', ''),
                    'keyword': tweet_data.get('keyword', ''),
                    'url': tweet_data.get('url', ''),
                })
            except Exception:
                pass
            continue
        if error_re.search(text) and 'scroll' not in text.lower():
            await _scrape_broadcast('log', {'msg': text, 'type': 'error'})
            continue
        m = done_re.search(text)
        if m:
            total_new = int(m.group(1))
            _scrape_state.update({'status': 'done', 'total_new': total_new})
            await _scrape_broadcast('done', {'total_new': total_new})
            continue
        await _scrape_broadcast('log', {'msg': text, 'type': 'info'})
    _scrape_state.update({'status': 'done', 'total_new': total_new})
    await _scrape_broadcast('done', {'total_new': total_new})


async def _scrape_runner(sid: str, cookies_file: str = 'cookies.json'):
    global _scrape_proc, _scrape_stop_event, _scrape_state
    _scrape_stop_event.clear()
    _scrape_state.update({'status': 'starting', 'current': 0, 'total': 0, 'total_new': 0})
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, str(PROJ / 'scripts' / 'scraper.py'),
            '--cookies', str(PROJ / cookies_file),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=str(PROJ),
            env={**os.environ, 'PYTHONUNBUFFERED': '1'},
        )
        _scrape_proc = proc
    except Exception as e:
        await _scrape_broadcast('error', {'msg': f'Failed to start: {e}'})
        return
    await _scrape_reader(proc)
    await proc.wait()
    _scrape_proc = None
    imported = _import_scraped_tweets(sid)
    if imported:
        await _scrape_broadcast('log', {'msg': f'Imported {imported} tweets to database', 'type': 'success'})


def _import_scraped_tweets(sid: str) -> int:
    json_path = PROJ / 'data' / 'comifuro_tweets.json'
    if not json_path.exists():
        return 0
    try:
        with open(json_path) as f:
            all_tweets = json.load(f)
    except (json.JSONDecodeError, Exception):
        return 0
    if not all_tweets:
        return 0
    db.add_tweets(sid, all_tweets)
    return len(all_tweets)


@router.post('/api/scrape/start')
async def api_scrape_start(request: Request):
    global _scrape_task
    if _scrape_task and not _scrape_task.done():
        return JSONResponse({'status': 'already_running'}, 409)
    sid = _session_required(request)
    if not sid:
        return JSONResponse({'status': 'error', 'msg': 'not authenticated'}, 401)

    try:
        body = await request.json()
        account_id = body.get('account_id')
        selected_kws = body.get('keywords')
    except Exception:
        account_id = None
        selected_kws = None

    if account_id:
        account = db.get_twitter_account(account_id)
        if not account:
            return JSONResponse({'status': 'error', 'msg': 'Account not found'}, 404)
        cookies_file = account.get('cookies_file') or f'cookies_{account_id}.json'
    else:
        cookies_file = 'cookies.json'

    cookies_path = PROJ / cookies_file
    if not cookies_path.exists():
        return JSONResponse({'status': 'error', 'msg': f'Cookies file "{cookies_file}" not found. Generate cookies first'}, 400)

    all_kws = db.get_keywords_with_priority(sid)
    priority_kws = {kw['keyword'] for kw in all_kws if kw['priority']}
    non_priority_kws = {kw['keyword'] for kw in all_kws if not kw['priority']}

    if selected_kws:
        selected_set = set(k.strip().lower() for k in selected_kws)
        priority_kws &= selected_set
        non_priority_kws &= selected_set

    keywords = list(priority_kws | non_priority_kws)
    for p in priority_kws:
        for c in non_priority_kws:
            combo = f'{p} {c}'
            if combo not in keywords:
                keywords.append(combo)

    with open(PROJ / 'keywords.txt', 'w') as f:
        f.write('\n'.join(keywords))
    _scrape_task = asyncio.create_task(_scrape_runner(sid, cookies_file))
    return {'status': 'started', 'session_id': sid, 'keywords': len(keywords)}


@router.post('/api/scrape/stop')
async def api_scrape_stop():
    global _scrape_proc
    if _scrape_proc:
        try:
            _scrape_proc.terminate()
            _scrape_proc = None
        except Exception:
            pass
    return {'status': 'stopped'}


@router.get('/api/scrape/status')
async def api_scrape_status():
    return {**_scrape_state, 'running': _scrape_task is not None and not _scrape_task.done()}


@router.get('/api/scrape/stream')
async def api_scrape_stream(request: Request):
    q: asyncio.Queue = asyncio.Queue()
    async with _scrape_lock:
        _scrape_subscribers.append(q)

    async def event_stream():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event_type, data = await asyncio.wait_for(q.get(), timeout=2)
                except asyncio.TimeoutError:
                    continue
                yield f'event: {event_type}\ndata: {json.dumps(data)}\n\n'
                if event_type == 'done':
                    break
        finally:
            async with _scrape_lock:
                try:
                    _scrape_subscribers.remove(q)
                except ValueError:
                    pass

    return StreamingResponse(
        event_stream(),
        media_type='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'X-Accel-Buffering': 'no'},
    )
