import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.helpers import jinja
from app.models import db
from app.routes import auth, pages, tweets, keywords, accounts, analysis, scrape, fandom

PROJ = Path(__file__).parent.parent

app = FastAPI(title='CF Scraper', docs_url=None)
app.mount('/static', StaticFiles(directory=str(PROJ / 'app' / 'static')), name='static')

app.include_router(auth.router)
app.include_router(pages.router)
app.include_router(tweets.router)
app.include_router(keywords.router)
app.include_router(accounts.router)
app.include_router(analysis.router)
app.include_router(scrape.router)
app.include_router(fandom.router)


@app.on_event('startup')
async def startup():
    db.init_db()


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('app.main:app', host='0.0.0.0', port=8000, reload=True, log_level='info')
