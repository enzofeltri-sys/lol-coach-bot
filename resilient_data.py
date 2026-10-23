import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from build_data import DDRAGON_VERSIONS, DDRAGON_BASE, CDRAGON_BASE, RUNE_RECOMMENDATIONS, HEADERS

PERKS_URLS = [
    CDRAGON_BASE.replace('/default/', '/fr_fr/') + '/perks.json',
    CDRAGON_BASE + '/perks.json',
]
NETWORK_ERRORS = (urllib.error.URLError, TimeoutError, OSError, ValueError)


def fetch(url):
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(request, timeout=20) as response:
                return json.loads(response.read().decode('utf-8'))
        except NETWORK_ERRORS as error:
            if isinstance(error, urllib.error.HTTPError) and error.code not in (408, 429, 500, 502, 503, 504):
                raise
            if attempt == 2:
                raise
            print('Static data retry ' + str(attempt + 1) + ': ' + type(error).__name__)
            time.sleep(2 ** attempt)


def describe(error):
    code = ' ' + str(error.code) if isinstance(error, urllib.error.HTTPError) else ''
    return type(error).__name__ + code


def optional(name, urls, check, sources, default):
    last = 'inconnu'
    for url in urls:
        try:
            value = fetch(url)
            if not check(value):
                raise ValueError('format inattendu')
            sources.append({'name': name, 'ok': True, 'detail': 'OK'})
            return value
        except NETWORK_ERRORS as error:
            last = describe(error)
    print('::warning::' + name + ' indisponible : ' + last)
    sources.append({'name': name, 'ok': False, 'detail': last})
    return default


def load_build_data():
    sources = []
    version = fetch(DDRAGON_VERSIONS)[0]
    base = DDRAGON_BASE.format(version=version)
    champions = fetch(base + '/champion.json')['data']
    runes = fetch(base + '/runesReforged.json')
    sources.append({'name': 'Data Dragon (champions, runes)', 'ok': True, 'detail': 'patch ' + version})
    recommendations = optional('CommunityDragon (recommandations de runes)', [RUNE_RECOMMENDATIONS], lambda v: isinstance(v, list) and len(v) > 0, sources, [])
    perks = optional('CommunityDragon (noms des éclats)', PERKS_URLS, lambda v: isinstance(v, list) and len(v) > 0, sources, [])
    perk_names = {str(p['id']): p['name'] for p in perks if isinstance(p, dict) and 'id' in p and 'name' in p}
    return {
        'version': version,
        'champions': champions,
        'items': {},
        'runes': runes,
        'rune_recommendations': recommendations,
        'perk_names': perk_names,
        'sources': sources,
        'generated_at': datetime.now(timezone.utc).strftime('%d/%m/%Y à %H:%M UTC'),
    }
