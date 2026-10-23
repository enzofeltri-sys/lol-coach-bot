import json
import time
import urllib.error
import urllib.request
from build_data import DDRAGON_VERSIONS, DDRAGON_BASE, RUNE_RECOMMENDATIONS, HEADERS


def fetch(url):
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(request, timeout=20) as response:
                return json.loads(response.read().decode('utf-8'))
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as error:
            if isinstance(error, urllib.error.HTTPError) and error.code not in (408, 429, 500, 502, 503, 504):
                raise
            if attempt == 2:
                raise
            print('Static data retry ' + str(attempt + 1) + ': ' + type(error).__name__)
            time.sleep(2 ** attempt)


def load_build_data():
    version = fetch(DDRAGON_VERSIONS)[0]
    base = DDRAGON_BASE.format(version=version)
    champions = fetch(base + '/champion.json')['data']
    runes = fetch(base + '/runesReforged.json')
    try:
        recommendations = fetch(RUNE_RECOMMENDATIONS)
        if not isinstance(recommendations, list):
            raise ValueError('Expected champion recommendation list')
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as error:
        print('::warning::CommunityDragon unavailable; rune recommendations omitted: ' + type(error).__name__)
        recommendations = []
    return {'version': version, 'champions': champions, 'items': {}, 'runes': runes, 'rune_recommendations': recommendations}
