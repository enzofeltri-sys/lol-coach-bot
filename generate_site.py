import os
import importlib.util
from pathlib import Path

from riot_api import get_puuid, get_ranked_match_ids, get_match
from analysis import analyze_matches
from report import build_report

spec = importlib.util.spec_from_file_location("lol_site_renderer", Path(__file__).with_name("site.py"))
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)
build_html = renderer.build_html

RIOT_ID = "Kyoraku#1707"
GAME_NAME, TAG_LINE = RIOT_ID.split("#")


def main():
    print(f"Analyse des games de {RIOT_ID}...")
    puuid = get_puuid(GAME_NAME, TAG_LINE)
    match_ids = get_ranked_match_ids(puuid, count=10)
    if not match_ids:
        raise RuntimeError("Aucune ranked récente trouvée.")
    matches = [get_match(match_id) for match_id in match_ids]
    analysis = analyze_matches(matches, puuid)
    os.makedirs("site", exist_ok=True)
    with open("rapport.md", "w", encoding="utf-8") as file:
        file.write(build_report(RIOT_ID, analysis))
    with open("site/index.html", "w", encoding="utf-8") as file:
        file.write(build_html(RIOT_ID, analysis))
    print("Rapport et site générés.")


if __name__ == "__main__":
    main()
