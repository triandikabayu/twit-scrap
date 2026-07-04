import re
from collections import Counter

import pandas as pd

ISO_PATTERNS = re.compile(
    r'(?:(?:cari|nyari|nc|mau beli|pengen beli|ada yang jual|looking for|where.*?buy|recommend)|'
    r'\b(wtb|wts|lf|iso)\b)',
    re.IGNORECASE
)

NOISE_WORDS = {
    'booth', 'tiket', 'ticket', 'merch', 'merchandise', 'single', 'preorder',
    'po', 'dong', 'dongg', 'kak', 'kakk', 'bang', 'bro', 'sis', 'mas', 'mbak',
    'harga', 'info', 'infokan', 'share', 'sharee', 'pliss', 'pls', 'please',
    'guys', 'kawan', 'temen', 'teman', 'ga', 'gak', 'gk', 'ngga', 'enggak',
    'bisa', 'gak', 'ada', 'di', 'ke', 'sih', 'deh', 'lah', 'yah', 'ya',
    'sapa', 'siapa', 'yang', 'juga', 'lagi', 'aja', 'a', 'the', 'at', 'for',
    'comifuro', 'cf22', 'cf', 'comipara', 'day', 'day1', 'day2', 'jual', 'beli',
    'cari', 'nyari', 'wtb', 'wts', 'lf', 'iso', 'nc', 'trading', 'trade',
    'vtuber', 'fanmade', 'fandom', 'katalog', 'brand', 'acara', 'event',
    'pax', 'rugi', 'adm', 'fee', 'dm', 'link', 'shopee', 'tokped',
    'slot', 'order', 'commission', 'comm', 'wt', 'jastip', 'titip',
    'ini', 'itu', 'saja', 'sudah', 'telah', 'akan', 'bisa', 'dapat',
    'tahun', 'bulan', 'minggu', 'hari', 'kemarin', 'besok', 'nanti',
    'baru', 'lama', 'banyak', 'sedikit', 'besar', 'kecil',
    'suka', 'sayang', 'mau', 'pengen', 'pake', 'pakai', 'punya',
    'namun', 'tapi', 'tetapi', 'sedangkan', 'sementara', 'karena',
    'jakarta', 'bandung', 'surabaya', 'jogja', 'yogya', 'bogor',
    'depok', 'tangsel', 'bekasi', 'jabodetabek', 'pusat', 'selatan',
    'utara', 'timur', 'barat', 'tengah',
    'you', 'your', 'our', 'their', 'this', 'that', 'these', 'those',
    'also', 'even', 'still', 'well', 'just', 'like', 'very', 'much',
    'may', 'june', 'july', 'august', 'april', 'maret', 'january',
    'february', 'march', 'september', 'october', 'november', 'december',
    'senin', 'selasa', 'rabu', 'kamis', 'jumat', 'sabtu', 'minggu',
    'lol', 'wkwk', 'wkwkwk', 'haha', 'hehe', 'xixi', 'huhu', 'hmm',
    'btw', 'otw', 'cmiiw', 'imo', 'imho', 'afaik', 'idk', 'tbh',
    'ya', 'iya', 'kalo', 'kalau', 'karna', 'karena', 'soalnya',
    'gue', 'gw', 'lo', 'lu', 'kita', 'kami', 'mereka',
    'hoyoverse', 'mihoyo', 'bandai', 'namco', 'sega', 'nintendo',
    'deltarune', 'undertale', 'fate', 'hololive', 'lovelive',
    'hearthstone', 'dota', 'valve', 'riot', 'epic',
    'yuri', 'yaoi', 'doujin', 'doujinshi', 'fanmerch', 'fanart',
    'fanmade', 'original', 'orivoca', 'voca',
    'hail', 'phm', 'project hail mary', 'orv', 'omniscient reader',
    'bl', 'gl', 'lgbt', 'lgbtq', 'pride', 'queer',
    'anime', 'manga', 'game', 'gacha', 'otome',
    'knight', 'knights', 'princess', 'prince', 'queen', 'king',
    'love', 'like', 'hate', 'want', 'need',
    'because', 'especially', 'however', 'therefore', 'furthermore',
    'moreover', 'meanwhile', 'otherwise', 'nevertheless',
    'aftersale', 'aftermarket', 'after', 'before',
    'catalog', 'catalogue', 'catalogs', 'stickers', 'sticker',
    'poster', 'posters', 'photo', 'photos', 'picture', 'pictures',
    'project', 'impact', 'universe', 'world', 'series',
    'masih', 'tetapi', 'terutama', 'setelah', 'sebelum',
    'sedangkan', 'sementara', 'sehingga', 'karena', 'namun',
    'tawarin', 'tawaran', 'ditawar', 'nego', 'negosiasi',
    'sample', 'contoh', 'display', 'displayed',
    'bundle', 'bundling', 'package', 'packaging',
    'order', 'orders', 'ordered', 'preorder', 'preorderr',
    'ready', 'stock', 'stocks', 'limited', 'exclusive',
    'special', 'discount', 'promo', 'voucher', 'coupon',
    'freebie', 'freebies', 'bonus', 'extra',
    'message', 'inbox', 'inquiry', 'inquiries',
    'comment', 'mention', 'reply', 'retweet', 'quote',
    'follow', 'followers', 'following', 'profile',
    'prize', 'price', 'prices', 'pricing',
    'shipping', 'delivery', 'courier', 'tracking',
    'condition', 'quality', 'original', 'genuine', 'authentic',
    'sealed', 'brand', 'mint', 'perfect', 'excellent',
    'urgent', 'important', 'serious', 'legit', 'trusted',
    'seller', 'buyer', 'shipper', 'admin', 'adm', 'oc', 'oc)',
    'payment', 'transfer', 'deposit', 'invoice', 'receipt',
    'warranty', 'guarantee', 'refund', 'exchange', 'return',
    'express', 'regular', 'economy', 'instant',
    'interested', 'interest', 'reserve', 'reserved',
    'sold', 'bought', 'listed', 'available',
    'update', 'reminder', 'deadline', 'bump',
    'nice', 'beautiful', 'cute', 'adorable', 'lovely', 'pretty',
    'cool', 'awesome', 'amazing', 'fantastic', 'wonderful',
    'gorgeous', 'stunning', 'splendid', 'excellent',
    'semoga', 'moga', 'mudah', 'cepat', 'laku',
    'indah', 'enak', 'manis', 'panas', 'dingin',
    'malam', 'siang', 'pagi', 'sore', 'petang',
    'waktu', 'tanggal', 'bulan', 'tahun',
    'semua', 'banyak', 'sedikit', 'beberapa',
    'tentang', 'antara', 'melalui', 'untuk',
    'dapat', 'harus', 'boleh', 'mungkin',
    'sekitar', 'kurang', 'lebih', 'paling', 'sangat',
    'selalu', 'jarang', 'sering', 'kadang',
    'comifuro', 'comipara', 'comic frontier',
    'booth', 'booths', 'event', 'acara',
    'pameran', 'festival', 'convention', 'con',
    'jastip', 'titip', 'trading', 'trade', 'trades',
    'open order', 'close order', 'slot', 'slots',
    'fanmade', 'fanmerch', 'merch', 'merchandise',
    'preferably', 'preferable', 'preference', 'preferences',
    'anything', 'anyone', 'anybody', 'anywhere',
    'everything', 'everyone', 'everybody', 'everywhere',
    'somewhere', 'somebody', 'someone', 'sometime',
    'nowhere', 'nothing', 'nobody', 'none',
    'already', 'always', 'almost', 'also', 'though',
    'however', 'whatever', 'whenever', 'wherever',
    'moreover', 'furthermore', 'meanwhile', 'otherwise',
    'nevertheless', 'nonetheless', 'notwithstanding',
    'therefore', 'thereby', 'therein', 'thereafter',
    'henceforth', 'hence', 'thus', 'thence',
    'furthermore', 'further', 'besides', 'likewise',
    'similarly', 'conversely', 'accordingly',
    'definitely', 'absolutely', 'certainly', 'surely',
    'probably', 'possibly', 'potentially', 'eventually',
    'ultimately', 'generally', 'typically', 'usually',
    'frequently', 'occasionally', 'seldom', 'rarely',
    'practically', 'basically', 'essentially',
    'particularly', 'specifically', 'especially',
    'significantly', 'considerably', 'substantially',
    'approximately', 'roughly', 'nearly', 'virtually',
    'meanwhile', 'late', 'early', 'soon', 'later',
    'earlier', 'sooner', 'ago', 'since', 'still',
    'yet', 'already', 'anyway', 'anyhow', 'anyways',
    'maybe', 'perhaps', 'probably', 'indeed',
    'surely', 'certainly', 'definitely',
    'please', 'pliss', 'plis', 'plisss',
    'urgent', 'emergency', 'critical', 'important',
    'besok', 'kemarin', 'nanti', 'tadi', 'ini', 'itu',
    'disini', 'disana', 'distu', 'disitu',
    'hope', 'hopes', 'hoped', 'hoping',
    'version', 'versions', 'ver', 'part', 'parts',
    'chapter', 'chapters', 'volume', 'volumes', 'episode',
    'season', 'series', 'edition', 'editions',
    'type', 'types', 'variant', 'variants',
    'anyang', 'selamat', 'siang', 'malam', 'pagi',
    'kaka', 'kakak', 'adek', 'adik', 'om', 'tante',
    'dakimakura', 'totebag', 'photocard', 'deskmat', 'artprint',
    'standee', 'keychain', 'gantungan', 'aksesoris', 'figurine',
    'cardboard', 'akrilik', 'acrylic', 'miniature',
    'sticker', 'stickers', 'stiker', 'shikishi',
    'musume', 'makura', 'dakimura',
    'priority', 'diutamakan', 'prioritas',
    'originals', 'original', 'sunday', 'monday',
    'booking', 'reserve', 'reserved',
    'midori', 'green', 'white', 'black', 'blue', 'red', 'pink',
    'colour', 'color', 'colors', 'colours',
    'oc', 'ocs', 'oc)', 'original character',
    'code', 'related', 'include', 'include',
    'diaries', 'book', 'books', 'reading',
    'endfield', 'field', 'work', 'project',
    'fast', 'easy', 'safe', 'cheap', 'best',
    'indonesia', 'indonesian',
    'haru', 'harus',
    'bubble', 'wrap', 'packaging', 'pack',
    'types', 'type', 'variant', 'variants',
    'waifu', 'husbando', 'husband',
    'holding', 'background', 'pouches', 'missing', 'mendapat',
    'nijisanji', 'anycolor', 'stamp', 'stamps', 'shipped',
    'changing', 'kamisama', 'jellyfish', 'highschool', 'medalis',
    'choco', 'chocolate', 'marshmallow', 'bubble',
    'gintama', 'akshsjdhd', 'hanya',
}

URGENCY_WORDS = {
    'desperate': 3, 'butuh banget': 3, 'nyari banget': 3,
    'cari mati-matian': 3, 'cari mati2an': 3,
    'plis bgt': 3, 'plis banget': 3, 'pliss banget': 3,
    'cari dari kmrn': 3, 'cari dari kemaren': 3, 'cari dari kemarin': 3,
    'nyari dari kmrn': 3, 'nyari dari kemaren': 3,
    'dm me please': 3, 'pengen bgt': 3, 'pingin bgt': 3,
    'butuh bgt': 3, 'butuh banget': 3, 'nyari bgt': 3,
    'please': 2, 'plis': 2, 'pliss': 2, 'banget': 2,
    'cari dong': 2, 'nyari dong': 2, 'tolong': 2,
    'ada yg jual': 2, 'ada yang jual': 2, 'ada gak': 2,
    'mau banget': 2, 'butuh': 2, 'butuh bgt': 2,
    'siapa yg jual': 2, 'ada yg punya': 2, 'ada yg jual gak': 2,
    'wtb': 1, 'wtt': 1, 'nc': 1, 'iso': 1, 'lf': 1,
    'cari': 1, 'nyari': 1, 'mau beli': 1, 'pengen beli': 1,
    'looking for': 1, 'open iso': 1, 'dm': 1, 'dm me': 1,
    'want to buy': 1, 'wants to buy': 1,
}


def find_iso_tweets(df):
    mask = df['full_text'].str.contains(ISO_PATTERNS, na=False)
    return df[mask].copy()


def classify_urgency(text):
    t = text.lower()
    score = 0
    for word, val in URGENCY_WORDS.items():
        if word in t:
            score += val
    if score >= 3:
        return 'Desperate', score
    elif score >= 1:
        return 'Normal', score
    return 'Santai', 0


def analyze_character_urgency(df_iso, all_found_counter, user_keywords=None):
    char_data = {}
    for _, row in df_iso.iterrows():
        text = row['full_text']
        label, score = classify_urgency(text)
        chars = extract_characters(text, user_keywords)
        for c in chars:
            if c not in char_data:
                char_data[c] = {'total': 0, 'desperate': 0, 'score_sum': 0}
            char_data[c]['total'] += 1
            char_data[c]['score_sum'] += score
            if label == 'Desperate':
                char_data[c]['desperate'] += 1
    return char_data


def extract_characters(text, user_keywords=None):
    found = set()
    text_lower = text.lower()
    iso_match = ISO_PATTERNS.search(text)

    if not iso_match:
        return []

    iso_pos = iso_match.end()
    context_after = text[iso_pos:iso_pos + 200].strip()
    context_before = text[max(0, iso_pos - 100):iso_pos].strip()

    _user_kw_lower = {k.lower() for k in (user_keywords or [])}

    # Match user keywords in text
    for kw in _user_kw_lower:
        if kw and len(kw) >= 2 and kw in text_lower:
            if kw not in NOISE_WORDS:
                found.add(kw.title())

    # "esp [name]" or "especially [name]"
    for esp_match in re.finditer(r'\besp\b\s+([A-Z]\w+(?:\s+[A-Z]\w+)?)', text[iso_pos:iso_pos + 200]):
        name = esp_match.group(1)
        found.add(name)

    # Capitalized words after ISO keyword
    caps_after = re.findall(r"[A-Z]\w+", context_after)
    for word in caps_after:
        w = word.lower()
        if w in _user_kw_lower or w in NOISE_WORDS or len(word) < 4 or word.startswith('http'):
            continue
        if len(word) <= 15:
            found.add(word)

    # Multi-word proper names
    multi = re.findall(r'[A-Z][a-z]+ [A-Z][a-z]+', context_after)
    for name in multi:
        w = name.lower()
        if any(w.startswith(nw) for nw in {'comifuro', 'comic', 'frontier', 'please', 'looking', 'jakarta', 'bandung'}):
            continue
        parts = w.split()
        if any(p in NOISE_WORDS for p in parts):
            continue
        if 6 <= len(name) <= 30:
            found.add(name)

    # Text in quotes after ISO keyword
    quoted = re.findall(r"[""''""](.+?)[""''""]", context_after)
    for q in quoted:
        q = q.strip()
        if not (3 <= len(q) <= 40) or q.lower().startswith('http'):
            continue
        ql = q.lower()
        if ql in NOISE_WORDS:
            continue
        if re.search(r'[A-Z]', q):
            found.add(q.title())

    # Parenthesized text after ISO keyword
    parenthesized = re.findall(r'\(([^)]+)\)', context_after)
    for p in parenthesized:
        p = p.strip()
        if not (3 <= len(p) <= 40) or p.lower().startswith('http'):
            continue
        pl = p.lower()
        if pl in NOISE_WORDS:
            continue
        if re.search(r'[A-Z]', p):
            words = p.split()
            if not any(w.lower() in NOISE_WORDS for w in words):
                found.add(p)

    # Clean up
    bad_tlds = {'.com', '.co', '.id', '.net', '.org', '.io', '.my'}
    cleaned = set()
    for name in found:
        nl = name.lower()
        if nl not in _user_kw_lower and nl in NOISE_WORDS:
            continue
        name_parts = nl.split()
        if len(name_parts) > 1 and any(p in NOISE_WORDS for p in name_parts):
            if nl not in _user_kw_lower:
                continue
        if len(name) < 4:
            continue
        if len(name) > 40:
            continue
        if any(t in nl for t in bad_tlds):
            continue
        if re.search(r'(comifuro|cf\d+|frontier|looking|please|katalog|merchandise|https?://)', nl):
            continue
        if re.match(r'^\d+', name):
            continue
        if re.match(r'^[A-Z]+$', name) and len(name) <= 2:
            continue
        cleaned.add(name)

    return list(cleaned)
