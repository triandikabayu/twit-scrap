"""
Consolidated twikit monkey patches for X.com API access.
These break when X updates its JS bundles — search for MONKEY_PATCH to find all patches.
"""

import re


# ── Patch 1: ON_DEMAND_FILE_REGEX ──
def patch_ondemand_regex():
    import twikit.x_client_transaction.transaction as _tx
    _tx.ON_DEMAND_FILE_REGEX = re.compile(
        r',(\d+):["\']ondemand\.s["\']', re.MULTILINE
    )
    _tx.ON_DEMAND_HASH_PATTERN = r',{}:"([0-9a-f]+)"'


# ── Patch 2: ClientTransaction.get_indices ──
def patch_get_indices():
    import twikit.x_client_transaction.transaction as _tx

    async def _patched_get_indices(self, home_page_response, session, headers):
        key_byte_indices = []
        response = self.validate_response(home_page_response) or self.home_page_response
        match_file = _tx.ON_DEMAND_FILE_REGEX.search(str(response))
        if not match_file:
            raise Exception("Couldn't find ondemand file index")
        on_demand_file_index = match_file.group(1)
        regex = re.compile(_tx.ON_DEMAND_HASH_PATTERN.format(on_demand_file_index))
        match_hash = regex.search(str(response))
        if not match_hash:
            raise Exception("Couldn't find hash for ondemand file")
        filename = match_hash.group(1)
        on_demand_file_url = f'https://abs.twimg.com/responsive-web/client-web/ondemand.s.{filename}a.js'
        on_demand_file_response = await session.request(method='GET', url=on_demand_file_url, headers=headers)
        matches = _tx.INDICES_REGEX.finditer(str(on_demand_file_response.text))
        for item in matches:
            key_byte_indices.append(item.group(2))
        if not key_byte_indices:
            raise Exception("Couldn't get KEY_BYTE indices")
        key_byte_indices = list(map(int, key_byte_indices))
        return key_byte_indices[0], key_byte_indices[1:]

    _tx.ClientTransaction.get_indices = _patched_get_indices


# ── Patch 3: GQLClient.search_timeline GET → POST ──
def patch_search_timeline():
    from twikit.client.gql import GQLClient, Endpoint
    from twikit.constants import FEATURES

    async def _patched_search_timeline(self, query: str, product: str, count: int, cursor: str | None):
        variables = {
            'rawQuery': query,
            'count': count,
            'querySource': 'typed_query',
            'product': product
        }
        if cursor is not None:
            variables['cursor'] = cursor
        return await self.gql_post(Endpoint.SEARCH_TIMELINE, variables, FEATURES)

    GQLClient.search_timeline = _patched_search_timeline


# ── Patch 4: User.__init__ KeyError fix ──
def patch_user_init():
    from twikit.user import User

    def _patched_user_init(self, client, data):
        self._client = client
        legacy = data['legacy']

        self.id: str = data['rest_id']
        self.created_at: str = legacy['created_at']
        self.name: str = legacy['name']
        self.screen_name: str = legacy['screen_name']
        self.profile_image_url: str = legacy['profile_image_url_https']
        self.profile_banner_url: str = legacy.get('profile_banner_url')
        self.url: str = legacy.get('url')
        self.location: str = legacy['location']
        self.description: str = legacy['description']

        entities = legacy.get('entities', {})
        self.description_urls: list = entities.get('description', {}).get('urls', [])
        self.urls: list = entities.get('url', {}).get('urls', [])

        self.pinned_tweet_ids: list[str] = legacy['pinned_tweet_ids_str']
        self.is_blue_verified: bool = data['is_blue_verified']
        self.verified: bool = legacy['verified']
        self.possibly_sensitive: bool = legacy['possibly_sensitive']
        self.can_dm: bool = legacy['can_dm']
        self.can_media_tag: bool = legacy['can_media_tag']
        self.want_retweets: bool = legacy['want_retweets']
        self.default_profile: bool = legacy['default_profile']
        self.default_profile_image: bool = legacy['default_profile_image']
        self.has_custom_timelines: bool = legacy['has_custom_timelines']
        self.followers_count: int = legacy['followers_count']
        self.fast_followers_count: int = legacy['fast_followers_count']
        self.normal_followers_count: int = legacy['normal_followers_count']
        self.following_count: int = legacy['friends_count']
        self.favourites_count: int = legacy['favourites_count']
        self.listed_count: int = legacy['listed_count']
        self.media_count = legacy['media_count']
        self.statuses_count: int = legacy['statuses_count']
        self.is_translator: bool = legacy['is_translator']
        self.translator_type: str = legacy['translator_type']
        self.withheld_in_countries: list[str] = legacy['withheld_in_countries']
        self.protected: bool = legacy.get('protected', False)

    User.__init__ = _patched_user_init


def apply_all_patches():
    patch_ondemand_regex()
    patch_get_indices()
    patch_search_timeline()
    patch_user_init()
