from collections import Counter

from fastapi import APIRouter, Request, Query

from app.helpers import _render, _session_required, _get_sid, PROJ
from app.models import db
from app.data import characters as ac

router = APIRouter()


@router.get('/api/top-chars')
async def api_top_chars(request: Request, limit: int = 15):
    sid = _session_required(request)
    if not sid:
        return []
    tweets = db.get_all_tweets_for_analysis(sid)
    if not tweets:
        return []
    import pandas as pd
    df = pd.DataFrame(tweets)
    df_iso = ac.find_iso_tweets(df)
    counter = Counter()
    for text in df_iso['full_text']:
        counter.update(ac.extract_characters(text))
    top = counter.most_common(limit)
    return [{'char': c, 'count': n} for c, n in top]


@router.get('/api/monthly-trend')
async def api_monthly_trend(request: Request):
    sid = _session_required(request)
    if not sid:
        return {'labels': [], 'values': []}
    tweets = db.get_all_tweets_for_analysis(sid)
    if not tweets:
        return {'labels': [], 'values': []}
    import pandas as pd
    df = pd.DataFrame(tweets)
    date_col = 'tweet_date' if 'tweet_date' in df.columns else 'date'
    df['_date'] = pd.to_datetime(df[date_col], errors='coerce')
    df['month'] = df['_date'].dt.to_period('M').astype(str)
    counts = df.dropna(subset=['month'])['month'].value_counts().sort_index()
    return {'labels': list(counts.index), 'values': [int(v) for v in counts.values]}


@router.get('/api/analysis')
async def api_analysis(request: Request):
    sid = _session_required(request)
    if not sid:
        return {'char_data': {}, 'urgency_dist': {}, 'total_iso': 0}
    return db.get_session_analysis(sid)
