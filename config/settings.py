import os

TWITTER_EMAIL = os.environ.get('TWITTER_EMAIL', '')
TWITTER_USERNAME = os.environ.get('TWITTER_USERNAME', '')
TWITTER_PASSWORD = os.environ.get('TWITTER_PASSWORD', '')

COOKIES_FILE = 'cookies.json'

DATE_FROM = '2024-01-01'
DATE_TO = '2026-12-31'

OUTPUT_CSV = 'data/comifuro_tweets.csv'
OUTPUT_JSON = 'data/comifuro_tweets.json'

SEARCH_COUNT = 20
RATE_LIMIT_SLEEP = 20
REQUEST_DELAY = (3, 7)

SESSION_EXPIRY_MINUTES = 30
