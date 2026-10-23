import os
import importlib.util
from pathlib import Path

from riot_api import get_puuid, get_ranked_match_ids, get_match, get_timeline
from analysis import analyze_matches
from report import build_report

spec = importlib.util.spec_from_file_location('lol_site_renderer', Path(__file__).with_name('site.py'))
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)

RIOT_ID = 'Kyoraku#1707'
GAME_NAME, TAG_LINE = RIOT_ID.split('#')
MATCH_COUNT = 20


def main():
    print(f'Analyse des {MATCH_COUNT} dernières games de {RIOT_ID}...')
    puuid = get_puuid(GAME_NAME, TAG_LINE)
    match_ids = get_ranked_match_ids(puuid, count=MATCH_COUNT)
    if not match_ids:
        raise RuntimeError('Aucune ranked récente trouvée.')
    matches = [get_match(match_id) for match_id in match_ids]
    timelines = {}
    timeline_errors = []
    for match in matches:
        match_id = match['metadata']['matchId']
        try:
            timelines[match_id] = get_timeline(match_id)
        except Exception as error:
            response = getattr(error, 'response', None)
            status = getattr(response, 'status_code', None)
            message = f'{match_id} : {type(error).__name__}' + (f' (HTTP {status})' if status else '')
            timeline_errors.append(message)
            print(f'Timeline indisponible : {message}')
    analysis = analyze_matches(matches, puuid, timelines, timeline_errors)
    os.makedirs('site', exist_ok=True)
    Path('rapport.md').write_text(build_report(RIOT_ID, analysis), encoding='utf-8')
    Path('site/index.html').write_text(renderer.build_html(RIOT_ID, analysis), encoding='utf-8')
    print('Rapport et site générés.')


if __name__ == '__main__':
    main()
