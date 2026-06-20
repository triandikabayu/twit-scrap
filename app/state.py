import asyncio

_scrape_proc: asyncio.subprocess.Process | None = None
_scrape_subscribers: list[asyncio.Queue] = []
_scrape_lock = asyncio.Lock()
_scrape_task: asyncio.Task | None = None
_scrape_stop_event = asyncio.Event()
_scrape_state = {'status': 'idle', 'current': 0, 'total': 0, 'total_new': 0, 'log': []}
