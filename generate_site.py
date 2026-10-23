import json
import os

from analysis import analyze_matches
from build_data import champion_build, load_build_data
from riot_api import fetch_recent_matches, fetch_match_details, fetch_match_timeline
from site import build_html


def main():
    riot_id = os.environ['RIOT_ID']
    game_name, tag_line = riot_id.split('#')
    puuid = fetch_puuid(game_name, tag_line)
    match_ids = fetch_recent_matches(puuid, count=20)
    matches = [fetch_match_details(match_id) for match_id in match_ids]
    timelines = {}
    timeline_errors = []
    for match_id in match_ids:
        try:
            timelines[match_id] = fetch_match_timeline(match_id)
        except Exception as error:
            timeline_errors.append(f'{match_id}: {error}')
    analysis = analyze_matches(matches, puuid, timelines, timeline_errors)
    build_data = load_build_data()
    first_game = analysis['games'][0]
    analysis['build'] = champion_build(first_game['champion'], first_game['role'], build_data)
    html = build_html(riot_id, analysis)
    output_path = os.environ.get('OUTPUT_PATH', 'index.html')
    with open(output_path, 'w', encoding='utf-8') as handle:
        handle.write(html)
    print(json.dumps({'riot_id': riot_id, 'games': len(matches), 'output': output_path}))


def fetch_puuid(game_name, tag_line):
    from riot_api import fetch_account
    return fetch_account(game_name, tag_line)['puuid']


if __name__ == '__main__':
    main()
