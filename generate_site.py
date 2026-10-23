import json
import os

from analysis import analyze_matches
from build_data import champion_build, load_build_data
from riot_api import get_puuid, get_ranked_match_ids, get_match, get_timeline
from site import build_html


def main():
    riot_id = os.environ['RIOT_ID']
    game_name, tag_line = riot_id.split('#')
    puuid = get_puuid(game_name, tag_line)
    match_ids = get_ranked_match_ids(puuid, count=20)
    matches = [get_match(match_id) for match_id in match_ids]
    timelines = {}
    timeline_errors = []
    for match_id in match_ids:
        try:
            timelines[match_id] = get_timeline(match_id)
        except Exception as error:
            timeline_errors.append(f'{match_id}: {error}')
    analysis = analyze_matches(matches, puuid, timelines, timeline_errors)
    build_data = load_build_data()
    first_game = analysis['games'][0]
    champion_key = next((key for key, champion in build_data['champions'].items() if champion['name'] == first_game['champion']), None)
    opponent_key = next((key for key, champion in build_data['champions'].items() if champion['name'] == first_game.get('opponent_champion')), None)
    if champion_key and opponent_key:
        analysis['build'] = champion_build(champion_key, first_game['role'], opponent_key, build_data)
    html = build_html(riot_id, analysis)
    output_path = os.environ.get('OUTPUT_PATH', 'index.html')
    with open(output_path, 'w', encoding='utf-8') as handle:
        handle.write(html)
    print(json.dumps({'riot_id': riot_id, 'games': len(matches), 'output': output_path}))


if __name__ == '__main__':
    main()
