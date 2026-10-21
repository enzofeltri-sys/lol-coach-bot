from statistics import mean


def find_player(match, puuid):
    for player in match["info"]["participants"]:
        if player["puuid"] == puuid:
            return player
    raise ValueError("Joueur introuvable dans ce match.")


def analyze_match(match, puuid):
    player = find_player(match, puuid)
    duration_min = match["info"]["gameDuration"] / 60

    kills = player["kills"]
    deaths = player["deaths"]
    assists = player["assists"]
    kda = (kills + assists) / max(deaths, 1)
    cs = player["totalMinionsKilled"] + player["neutralMinionsKilled"]
    cs_per_min = cs / duration_min
    wards_per_min = player["wardsPlaced"] / duration_min

    return {
        "champion": player["championName"],
        "role": player["teamPosition"],
        "win": player["win"],
        "kills": kills,
        "deaths": deaths,
        "assists": assists,
        "kda": round(kda, 2),
        "cs": cs,
        "cs_per_min": round(cs_per_min, 2),
        "wards": player["wardsPlaced"],
        "wards_per_min": round(wards_per_min, 2),
        "damage": player["totalDamageDealtToChampions"],
        "dragons": player["dragonKills"],
        "barons": player["baronKills"],
        "duration_min": round(duration_min, 1),
    }


def analyze_matches(matches, puuid):
    games = [analyze_match(match, puuid) for match in matches]
    deaths = [game["deaths"] for game in games]
    cs = [game["cs_per_min"] for game in games]
    wards = [game["wards_per_min"] for game in games]
    kda = [game["kda"] for game in games]

    issues = []
    if mean(deaths) >= 5:
        issues.append("Tu meurs trop souvent : vise moins de 4 morts par game.")
    if mean(cs) < 6:
        issues.append("Ton farm est faible : vise au moins 6 CS par minute.")
    if mean(wards) < 0.8:
        issues.append("Ta vision est insuffisante : vise au moins 0,8 ward par minute.")
    if mean(kda) < 2:
        issues.append("Ton impact en fight est faible : cherche plus d'assists et évite les fights isolés.")

    strengths = []
    if mean(cs) >= 6:
        strengths.append("Ton farm est correct.")
    if mean(wards) >= 0.8:
        strengths.append("Tu poses une quantité correcte de vision.")
    if mean(kda) >= 2.5:
        strengths.append("Ton KDA global est solide.")

    return {
        "games": games,
        "avg_deaths": round(mean(deaths), 2),
        "avg_cs_per_min": round(mean(cs), 2),
        "avg_wards_per_min": round(mean(wards), 2),
        "avg_kda": round(mean(kda), 2),
        "win_rate": round(100 * sum(game["win"] for game in games) / len(games)),
        "issues": issues or ["Aucun problème majeur détecté sur ces games."],
        "strengths": strengths or ["Continue à jouer régulièrement pour établir une base statistique."],
    }
