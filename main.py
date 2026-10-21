from riot_api import get_puuid, get_ranked_match_ids, get_match
from analysis import analyze_matches
from report import build_report

RIOT_ID = "Kyoraku#1707"
GAME_NAME, TAG_LINE = RIOT_ID.split("#")


def main():
    print(f"Analyse des games de {RIOT_ID}...")
    puuid = get_puuid(GAME_NAME, TAG_LINE)
    match_ids = get_ranked_match_ids(puuid, count=10)

    if not match_ids:
        print("Aucune ranked récente trouvée.")
        return

    matches = [get_match(match_id) for match_id in match_ids]
    analysis = analyze_matches(matches, puuid)
    report = build_report(RIOT_ID, analysis)

    with open("rapport.md", "w", encoding="utf-8") as file:
        file.write(report)

    print("Rapport généré : rapport.md")


if __name__ == "__main__":
    main()
