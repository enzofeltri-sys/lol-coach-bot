import importlib.util
import json
import os

from analysis import analyze_matches
from resilient_data import load_build_data
from duel_ui import prepare_duels, attach_duels
from progress import build_progress, attach_plan
from riot_api import get_puuid, get_ranked_match_ids, get_match, get_timeline


def load_local_site_module():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'site.py')
    spec = importlib.util.spec_from_file_location('lol_site', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build_html = load_local_site_module().build_html


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
    builds = prepare_duels(analysis['games'], build_data)
    analysis['build'] = builds[0] if builds else {}
    progress = build_progress(analysis['games'])
    html = build_html(riot_id, analysis)
    html = attach_plan(html, progress)
    html = attach_duels(html, builds, build_data)
    output_path = os.environ.get('OUTPUT_PATH', 'site/index.html')
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as handle:
        handle.write(html)
    top = progress['priority']
    print(json.dumps({'champions': len(builds), 'diagnostics': build_data.get('diagnostics'), 'sources': build_data.get('sources'), 'plan': {'games': progress['games'], 'priority': top['key'] if top else None, 'trend': top['trend'] if top else None}}, ensure_ascii=False))


if __name__ == '__main__':
    main()
