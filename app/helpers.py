import re
from pathlib import Path
from datetime import datetime

from fastapi import Request
from jinja2 import Environment, FileSystemLoader

from app.models import db
from config import settings as config

PROJ = Path(__file__).parent.parent

_PRIORITY_RE = re.compile(
    r'(#?wtb|#?wts|#?wtt|cf\s*22|comifuro|comic\s*frontier|'
    r'catalog(ue)?|merch|booth|haul|purchase|beli|borong|'
    r'sold\s*out|habis|artist\s*alley|fandom)',
    re.IGNORECASE
)

jinja = Environment(loader=FileSystemLoader(str(PROJ / 'app' / 'templates')))
jinja.globals['now'] = datetime.now


def _render(name: str, **kw) -> str:
    return jinja.get_template(name).render(**kw)


def _get_sid(request: Request) -> str:
    return request.cookies.get('cf_session') or request.query_params.get('session_id') or request.headers.get('x-session-id', '')


def _session_required(request: Request):
    sid = _get_sid(request)
    if not sid or not db.verify_session(sid):
        return None
    return sid


def _get_session_remaining(sid: str) -> int:
    conn = db.get_db()
    row = conn.execute(
        'SELECT CAST((julianday(\'now\') - julianday(last_seen)) * 86400 AS INTEGER) as elapsed FROM sessions WHERE id = ?',
        (sid,)
    ).fetchone()
    conn.close()
    if not row:
        return 0
    remaining = (config.SESSION_EXPIRY_MINUTES * 60) - row['elapsed']
    return max(remaining, 0)
