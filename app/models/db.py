import hashlib
import os
import sqlite3
import uuid
from collections import Counter
from pathlib import Path
from typing import Optional

from config import settings as config

DB_PATH = Path(__file__).parent / 'data' / 'cf_scraper.db'


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA foreign_keys=ON')
    return conn


def _hash_password(password: str) -> str:
    return hashlib.sha256((password + 'cf-scraper-salt-2024').encode()).hexdigest()


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            display_name TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL REFERENCES users(username),
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            last_seen TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS tweets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL REFERENCES sessions(id),
            tweet_id TEXT,
            full_text TEXT,
            user_screen_name TEXT,
            user_name TEXT,
            tweet_date TEXT,
            favorite_count INTEGER DEFAULT 0,
            retweet_count INTEGER DEFAULT 0,
            url TEXT,
            keyword TEXT,
            posted_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL REFERENCES sessions(id),
            keyword TEXT NOT NULL,
            priority INTEGER NOT NULL DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(session_id, keyword)
        );

        CREATE INDEX IF NOT EXISTS idx_tweets_session ON tweets(session_id);
        CREATE INDEX IF NOT EXISTS idx_keywords_session ON keywords(session_id);

        CREATE TABLE IF NOT EXISTS twitter_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT REFERENCES sessions(id),
            name TEXT NOT NULL,
            email TEXT NOT NULL DEFAULT '',
            username TEXT NOT NULL,
            password TEXT NOT NULL DEFAULT '',
            cookies_file TEXT NOT NULL DEFAULT '',
            is_default INTEGER NOT NULL DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );
    ''')
    conn.commit()
    # Add priority column if missing (existing databases)
    try:
        conn.execute('ALTER TABLE keywords ADD COLUMN priority INTEGER NOT NULL DEFAULT 0')
        conn.commit()
    except sqlite3.OperationalError:
        pass
    # Add twitter_accounts table if missing (existing databases)
    try:
        conn.execute('SELECT id FROM twitter_accounts LIMIT 1').fetchall()
    except sqlite3.OperationalError:
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS twitter_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT REFERENCES sessions(id),
                name TEXT NOT NULL,
                email TEXT NOT NULL DEFAULT '',
                username TEXT NOT NULL,
                password TEXT NOT NULL DEFAULT '',
                cookies_file TEXT NOT NULL DEFAULT '',
                is_default INTEGER NOT NULL DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now'))
            )
        ''')
        if config.TWITTER_USERNAME:
            conn.execute(
                'INSERT INTO twitter_accounts (name, email, username, password, cookies_file, is_default) VALUES (?, ?, ?, ?, ?, 1)',
                ('Default', config.TWITTER_EMAIL, config.TWITTER_USERNAME, config.TWITTER_PASSWORD, 'cookies.json')
            )
        conn.commit()
    # Seed default Twitter account from config
    if config.TWITTER_USERNAME:
        row = conn.execute('SELECT id FROM twitter_accounts WHERE is_default = 1 LIMIT 1').fetchone()
        if not row:
            conn.execute(
                'INSERT INTO twitter_accounts (session_id, name, email, username, password, cookies_file, is_default) VALUES (NULL, ?, ?, ?, ?, ?, 1)',
                ('Default', config.TWITTER_EMAIL, config.TWITTER_USERNAME, config.TWITTER_PASSWORD, 'cookies.json')
            )
            conn.commit()
    conn.close()


# ── Auth ──

def register_user(username: str, password: str) -> str | None:
    username = username.strip().lower()
    if not username or not password:
        return None
    conn = get_db()
    try:
        conn.execute(
            'INSERT INTO users (username, password_hash, display_name) VALUES (?, ?, ?)',
            (username, _hash_password(password), username)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return None  # username taken
    # Create session for user
    sid = uuid.uuid4().hex[:12]
    conn.execute('INSERT INTO sessions (id, username) VALUES (?, ?)', (sid, username))
    conn.commit()
    conn.close()
    return sid


def login_user(username: str, password: str) -> str | None:
    username = username.strip().lower()
    conn = get_db()
    row = conn.execute(
        'SELECT password_hash FROM users WHERE username = ?', (username,)
    ).fetchone()
    if not row:
        conn.close()
        return None
    if row['password_hash'] != _hash_password(password):
        conn.close()
        return None
    # Create new session
    sid = uuid.uuid4().hex[:12]
    conn.execute('INSERT INTO sessions (id, username) VALUES (?, ?)', (sid, username))
    conn.commit()
    conn.close()
    return sid


def get_session_user(sid: str) -> str | None:
    conn = get_db()
    row = conn.execute('SELECT username FROM sessions WHERE id = ?', (sid,)).fetchone()
    conn.close()
    return row['username'] if row else None


def verify_session(sid: str) -> bool:
    conn = get_db()
    cutoff = f'-{config.SESSION_EXPIRY_MINUTES} minutes'
    row = conn.execute(
        'SELECT id FROM sessions WHERE id = ? AND last_seen >= datetime(\'now\', ?)',
        (sid, cutoff)
    ).fetchone()
    if row:
        conn.execute('UPDATE sessions SET last_seen = datetime(\'now\') WHERE id = ?', (sid,))
        conn.commit()
    else:
        conn.execute('DELETE FROM sessions WHERE id = ?', (sid,))
        conn.commit()
    conn.close()
    return row is not None


def cleanup_expired_sessions():
    conn = get_db()
    cutoff = f'-{config.SESSION_EXPIRY_MINUTES} minutes'
    conn.execute(
        'DELETE FROM sessions WHERE last_seen < datetime(\'now\', ?)',
        (cutoff,)
    )
    conn.commit()
    conn.close()


# ── Sessions ──

def get_user_session(username: str) -> str:
    """Get latest session for a user."""
    username = username.strip().lower()
    conn = get_db()
    row = conn.execute(
        'SELECT id FROM sessions WHERE username = ? ORDER BY last_seen DESC LIMIT 1',
        (username,)
    ).fetchone()
    if row:
        sid = row['id']
        conn.execute('UPDATE sessions SET last_seen = datetime(\'now\') WHERE id = ?', (sid,))
        conn.commit()
        conn.close()
        return sid
    # Create new session
    sid = uuid.uuid4().hex[:12]
    conn.execute('INSERT INTO sessions (id, username) VALUES (?, ?)', (sid, username))
    conn.commit()
    conn.close()
    return sid


# ── Tweets ── (unchanged, all take session_id)

def add_tweets(sid: str, tweets: list[dict]):
    conn = get_db()
    for t in tweets:
        try:
            conn.execute('''
                INSERT OR IGNORE INTO tweets
                (session_id, tweet_id, full_text, user_screen_name, user_name,
                 tweet_date, favorite_count, retweet_count, url, keyword)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                sid,
                t.get('id', '') or t.get('tweet_id', ''),
                t.get('full_text', ''),
                t.get('user_screen_name', ''),
                t.get('user_name', ''),
                t.get('date', '') or t.get('tweet_date', ''),
                int(t.get('favorite_count', 0) or 0),
                int(t.get('retweet_count', 0) or 0),
                t.get('url', ''),
                t.get('keyword', ''),
            ))
        except Exception:
            pass
    conn.commit()
    conn.close()


def get_tweets(sid: str, q: str = '', keyword: str = '', char: str = '',
               page: int = 1, limit: int = 20,
               user_keywords: list[str] | None = None) -> tuple[list[dict], int]:
    conn = get_db()
    conditions = ['session_id = ?']
    params = [sid]

    if q:
        conditions.append('full_text LIKE ?')
        params.append(f'%{q}%')
    if keyword:
        conditions.append('keyword = ?')
        params.append(keyword)

    where = ' AND '.join(conditions)

    if not char:
        total = conn.execute(f'SELECT COUNT(*) FROM tweets WHERE {where}', params).fetchone()[0]
        offset = (page - 1) * limit
        rows = conn.execute(
            f'SELECT * FROM tweets WHERE {where} ORDER BY id DESC LIMIT ? OFFSET ?',
            params + [limit, offset]
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows], total

    # Char filter: fetch ALL matching tweets, filter by character, then paginate
    rows = conn.execute(
        f'SELECT * FROM tweets WHERE {where} ORDER BY id DESC', params
    ).fetchall()
    conn.close()

    cl = char.lower()
    from app.data import characters as ac
    all_tweets = [dict(r) for r in rows]
    filtered = []
    for t in all_tweets:
        text = t.get('full_text', '')
        chars = ac.extract_characters(text, user_keywords=user_keywords)
        if any(cl == c.lower() for c in chars):
            filtered.append(t)

    total = len(filtered)
    offset = (page - 1) * limit
    result = [dict(r) for r in filtered[offset:offset + limit]]
    return result, total


def get_all_tweets_for_analysis(sid: str) -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        'SELECT * FROM tweets WHERE session_id = ? ORDER BY id', (sid,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Keywords ──

def get_keywords(sid: str) -> list[str]:
    conn = get_db()
    rows = conn.execute(
        'SELECT keyword, priority FROM keywords WHERE session_id = ? ORDER BY priority DESC, keyword',
        (sid,)
    ).fetchall()
    conn.close()
    return [r['keyword'] for r in rows]
    # priority is available but not returned in the simple list


def get_keywords_with_priority(sid: str) -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        'SELECT keyword, priority FROM keywords WHERE session_id = ? ORDER BY priority DESC, keyword',
        (sid,)
    ).fetchall()
    conn.close()
    return [{'keyword': r['keyword'], 'priority': bool(r['priority'])} for r in rows]


def add_keywords(sid: str, keywords: list[str], priority: int = 0) -> list[str]:
    conn = get_db()
    added = []
    for kw in keywords:
        kw = kw.strip().lower()
        if not kw:
            continue
        try:
            conn.execute(
                'INSERT INTO keywords (session_id, keyword, priority) VALUES (?, ?, ?)',
                (sid, kw, priority)
            )
            added.append(kw)
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    conn.close()
    return added


def update_keyword_priority(sid: str, keyword: str, priority: int):
    conn = get_db()
    conn.execute(
        'UPDATE keywords SET priority = ? WHERE session_id = ? AND keyword = ?',
        (priority, sid, keyword.strip().lower())
    )
    conn.commit()
    conn.close()


def delete_keywords(sid: str, keywords: list[str]):
    conn = get_db()
    for kw in keywords:
        conn.execute(
            'DELETE FROM keywords WHERE session_id = ? AND keyword = ?',
            (sid, kw.strip().lower())
        )
    conn.commit()
    conn.close()


def delete_tweets(sid: str, keyword: str = '', char: str = '') -> int:
    conn = get_db()
    query = 'DELETE FROM tweets WHERE session_id = ?'
    params = [sid]
    if keyword:
        query += ' AND keyword = ?'
        params.append(keyword.lower())
    if char:
        query += ' AND LOWER(full_text) LIKE ?'
        params.append(f'%{char.lower()}%')
    conn.execute(query, params)
    deleted = conn.total_changes
    conn.commit()
    conn.close()
    return deleted


def get_tweets_summary(sid: str) -> dict:
    conn = get_db()
    keywords = conn.execute(
        'SELECT keyword, COUNT(*) as cnt FROM tweets WHERE session_id = ? GROUP BY keyword ORDER BY cnt DESC',
        (sid,)
    ).fetchall()
    conn.close()
    return {
        'keywords': [{'keyword': r[0], 'count': r[1]} for r in keywords],
    }


# ── Stats / Analysis ──

def get_session_stats(sid: str) -> dict:
    tweets = get_all_tweets_for_analysis(sid)
    total = len(tweets)
    kw_list = get_keywords(sid)
    if total == 0:
        return {'total_tweets': 0, 'iso_tweets': 0, 'unique_chars': 0, 'keywords': len(kw_list), 'keyword_list': kw_list}

    import pandas as pd
    from app.data import characters as ac
    df = pd.DataFrame(tweets)
    df_iso = ac.find_iso_tweets(df)
    all_found = []
    for text in df_iso['full_text']:
        all_found.extend(ac.extract_characters(text))

    return {
        'total_tweets': total,
        'iso_tweets': len(df_iso),
        'unique_chars': len(set(all_found)),
        'keywords': len(kw_list),
        'keyword_list': kw_list,
    }


def get_session_analysis(sid: str) -> dict:
    tweets = get_all_tweets_for_analysis(sid)
    if not tweets:
        return {'char_data': {}, 'urgency_dist': {}, 'total_iso': 0}

    import pandas as pd
    from app.data import characters as ac
    df = pd.DataFrame(tweets)
    df_iso = ac.find_iso_tweets(df)

    urgency_labels = []
    for text in df_iso['full_text']:
        label, _ = ac.classify_urgency(text)
        urgency_labels.append(label)

    # Get user's non-priority keywords as additional character names
    user_keywords = [kw['keyword'] for kw in get_keywords_with_priority(sid) if not kw['priority']]

    return {
        'char_data': ac.analyze_character_urgency(df_iso, Counter(), user_keywords=user_keywords),
        'urgency_dist': dict(Counter(urgency_labels)),
        'total_iso': len(df_iso),
    }


# ── Twitter Accounts ──

def get_twitter_accounts() -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        'SELECT * FROM twitter_accounts ORDER BY is_default DESC, id'
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_twitter_account(name: str, email: str, username: str, password: str) -> int | None:
    conn = get_db()
    try:
        conn.execute(
            'INSERT INTO twitter_accounts (session_id, name, email, username, password) VALUES (NULL, ?, ?, ?, ?)',
            (name, email, username, password)
        )
        conn.commit()
        aid = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        conn.close()
        return aid
    except sqlite3.IntegrityError:
        conn.close()
        return None


def delete_twitter_account(account_id: int) -> bool:
    conn = get_db()
    row = conn.execute(
        'DELETE FROM twitter_accounts WHERE id = ? AND is_default = 0',
        (account_id,)
    )
    deleted = row.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def get_twitter_account(account_id: int) -> dict | None:
    conn = get_db()
    row = conn.execute(
        'SELECT * FROM twitter_accounts WHERE id = ?',
        (account_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def update_account_cookies(account_id: int, cookies_file: str):
    conn = get_db()
    conn.execute(
        'UPDATE twitter_accounts SET cookies_file = ? WHERE id = ?',
        (cookies_file, account_id)
    )
    conn.commit()
    conn.close()
