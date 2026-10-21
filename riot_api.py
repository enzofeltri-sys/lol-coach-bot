import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("RIOT_API_KEY")
if not API_KEY:
    raise RuntimeError("RIOT_API_KEY est absente. Crée un fichier .env.")

HEADERS = {"X-Riot-Token": API_KEY}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)


def get_json(url, params=None):
    response = SESSION.get(url, params=params, timeout=20)
    if response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", "2"))
        time.sleep(retry_after)
        response = SESSION.get(url, params=params, timeout=20)
    response.raise_for_status()
    return response.json()


def get_puuid(game_name, tag_line):
    url = f"https://europe.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
    return get_json(url)["puuid"]


def get_ranked_match_ids(puuid, count=10):
    url = f"https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids"
    return get_json(url, {"queue": 420, "type": "ranked", "start": 0, "count": count})


def get_match(match_id):
    url = f"https://europe.api.riotgames.com/lol/match/v5/matches/{match_id}"
    return get_json(url)


def get_timeline(match_id):
    url = f"https://europe.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline"
    return get_json(url)
