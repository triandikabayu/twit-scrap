from fastapi import APIRouter

from app.data.fandoms import search_local, search_wikipedia

router = APIRouter()


@router.post('/api/fandom/search')
async def api_fandom_search(body: dict):
    fandom = body.get('fandom', '').strip()
    if not fandom:
        return {'error': 'No fandom name provided'}
    chars = search_local(fandom)
    if chars:
        return {'characters': [{'name': c, 'source': 'database'} for c in chars], 'source': 'database'}
    try:
        wiki_results = search_wikipedia(fandom)
        if wiki_results:
            return {'characters': wiki_results, 'source': 'wikipedia'}
    except Exception:
        pass
    return {'characters': [], 'source': 'none'}
